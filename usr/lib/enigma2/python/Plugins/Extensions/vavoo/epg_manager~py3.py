"""
EPG Manager - Optimized EPG download and caching module.

Features:
- Local disk cache with configurable TTL
- Streaming download with on-the-fly decompression
- Retry with exponential backoff
- Memory-efficient XML parsing
- Program filtering (only current/future programs)
"""
# mod lululla 20260314
# Python 2/3 compatibility
import gzip
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path
import logging
import json
import io
import re
import time
from typing import Optional, Dict, List, Tuple, Set
from dataclasses import dataclass
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@dataclass
class EPGSource:
    """Configuration for an EPG source."""
    name: str
    url: str
    backup_url: Optional[str] = None
    enabled: bool = True
    priority: int = 0
    country_code: str = ""


@dataclass
class ChannelInfo:
    """EPG channel information."""
    id: str
    display_name: str
    icon: Optional[str] = None
    normalized_name: str = ""
    country_code: str = ""


@dataclass
class Program:
    """EPG program information."""
    channel_id: str
    start: datetime
    stop: datetime
    title: str
    desc: str = ""

    def is_current_or_future(self, now: datetime) -> bool:
        """Check if program is currently running or in the future."""
        return self.stop > now


class EPGCache:
    """Manages local EPG cache on disk."""

    def __init__(self, cache_dir: Optional[Path] = None, ttl_hours: int = 12):
        self.cache_dir = cache_dir or Path.home() / ".cache" / "vavoo_epg"
        self.ttl = timedelta(hours=ttl_hours)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, source_name):
        return self.cache_dir / "{}_epg.xml".format(source_name)

    def _get_meta_path(self, source_name):
        return self.cache_dir / "{}_meta.json".format(source_name)

    def is_valid(self, source_name: str) -> bool:
        """Check if cached EPG is still valid."""
        meta_path = self._get_meta_path(source_name)
        cache_path = self._get_cache_path(source_name)

        if not meta_path.exists() or not cache_path.exists():
            return False

        try:
            with open(meta_path, 'r') as f:
                meta = json.load(f)
            cached_time = datetime.fromisoformat(meta['timestamp'])
            return datetime.now(timezone.utc) - cached_time < self.ttl
        except Exception:
            return False

    def get_cached(self, source_name: str) -> Optional[bytes]:
        """Get cached EPG content if valid."""
        if not self.is_valid(source_name):
            return None

        cache_path = self._get_cache_path(source_name)
        try:
            with open(cache_path, 'rb') as f:
                return f.read()
        except Exception as e:
            logging.warning("Failed to read cache: {}".format(e))
            return None

    def save(self, source_name: str, content: bytes) -> bool:
        """Save EPG content to cache."""
        cache_path = self._get_cache_path(source_name)
        meta_path = self._get_meta_path(source_name)

        try:
            with open(cache_path, 'wb') as f:
                f.write(content)
            with open(meta_path, 'w') as f:
                json.dump({
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'size': len(content)
                }, f)
            return True
        except Exception as e:
            logging.error("Failed to save cache: {}".format(e))
            return False

    def clear(self, source_name: Optional[str] = None):
        """Clear cache for specific source or all."""
        if source_name:
            self._get_cache_path(source_name).unlink(missing_ok=True)
            self._get_meta_path(source_name).unlink(missing_ok=True)
        else:
            for f in self.cache_dir.glob("*_epg.xml"):
                f.unlink()
            for f in self.cache_dir.glob("*_meta.json"):
                f.unlink()


class EPGDownloader:
    """Handles EPG download with retry and streaming."""

    DEFAULT_USER_AGENT = "VAVOO/2.6"
    MAX_RETRIES = 3
    RETRY_DELAY = 2.0
    RETRY_BACKOFF = 2.0
    TIMEOUT = 30
    CHUNK_SIZE = 65536  # 64KB chunks

    def __init__(self, user_agent: str = DEFAULT_USER_AGENT):
        self.user_agent = user_agent
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': user_agent})

    def _download_with_retry(self, url):
        """Download with exponential backoff retry."""
        delay = self.RETRY_DELAY

        for attempt in range(self.MAX_RETRIES):
            try:
                logging.info(
                    "Downloading EPG from {} (attempt {})...".format(
                        url, attempt + 1))

                response = self.session.get(
                    url,
                    timeout=self.TIMEOUT,
                    verify=False,
                    stream=True
                )
                response.raise_for_status()

                # Stream download to memory
                content = io.BytesIO()
                total = 0

                for chunk in response.iter_content(chunk_size=self.CHUNK_SIZE):
                    if chunk:
                        content.write(chunk)
                        total += len(chunk)

                result = content.getvalue()
                logging.info(
                    "Downloaded {} bytes from {}".format(
                        len(result), url))

                if len(result) < 1024:
                    raise ValueError(
                        "Download too small: {} bytes".format(
                            len(result)))

                return result

            except Exception as e:
                logging.warning(
                    "Download failed (attempt {}): {}".format(
                        attempt + 1, e))
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(delay)
                    delay *= self.RETRY_BACKOFF

        return None

    def download(self, source):
        """Download EPG from source with fallback."""
        content = self._download_with_retry(source.url)

        if content is None and source.backup_url:
            logging.info("Trying backup URL for {}...".format(source.name))
            content = self._download_with_retry(source.backup_url)

        return content

    def decompress(self, content, url):
        """Decompress gzipped content if needed."""
        try:
            if url.endswith('.gz'):
                logging.debug("Decompressing GZIP content...")
                return gzip.decompress(content)
            return content
        except Exception as e:
            logging.error("Decompression failed: {}".format(e))
            return None


class EPGParser:
    """Efficient XMLTV parser with filtering."""

    # Only keep programs within this time window
    PROGRAM_WINDOW_HOURS = 24 * 7  # 7 days

    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalize channel name for matching."""
        if not name:
            return ""
        n = name.upper().strip()

        # Remove country prefixes
        n = re.sub(r'^(IT|CH)\s*-\s*', '', n, flags=re.IGNORECASE)

        # Remove quality suffixes
        n = re.sub(r'\s+(HD|FHD|SD|HEVC|H265|4K).*', '', n)

        # Remove special chars
        n = re.sub(r'[^A-Z0-9]', '', n)

        return n.strip()

    @staticmethod
    def parse_xmltv_date(date_str: str) -> Optional[datetime]:
        """Parse XMLTV date format."""
        if not date_str:
            return None
        try:
            # Format: YYYYMMDDHHMMSS +ZZZZ
            return datetime.strptime(date_str, "%Y%m%d%H%M%S %z")
        except ValueError:
            try:
                # Try without timezone
                dt = datetime.strptime(date_str[:14], "%Y%m%d%H%M%S")
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                return None

    def parse(self,
              xml_content: bytes,
              source_name: str = "",
              country_code: str = None,
              filter_channels: Optional[Set[str]] = None) -> Tuple[Dict[str,
                                                                        ChannelInfo],
                                                                   Dict[str,
                                                                        List[Program]]]:
        """Parse XMLTV content efficiently.

        Returns:
            Tuple of (channels_dict, programs_dict)
        """
        channels: Dict[str, ChannelInfo] = {}
        programs: Dict[str, List[Program]] = {}

        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(hours=self.PROGRAM_WINDOW_HOURS)

        try:
            # Use iterparse for memory efficiency
            context = ET.iterparse(
                io.BytesIO(xml_content), events=(
                    'start', 'end'))

            for event, elem in context:
                if event == 'start':
                    continue

                if elem.tag == 'channel':
                    channel_id = elem.get('id')
                    if not channel_id:
                        elem.clear()
                        continue

                    display_name_elem = elem.find('display-name')
                    display_name = display_name_elem.text if display_name_elem is not None else ""

                    # Filter Swiss channels (RSI only)
                    if "Swiss" in source_name or "RSI" in source_name:
                        norm = self.normalize_name(display_name)
                        if norm not in ["RSILA1", "RSILA2"]:
                            elem.clear()
                            continue

                    icon_elem = elem.find('icon')
                    icon = icon_elem.get(
                        'src') if icon_elem is not None else None

                    channels[channel_id] = ChannelInfo(
                        id=channel_id,
                        display_name=display_name,
                        icon=icon,
                        normalized_name=self.normalize_name(display_name),
                        country_code=country_code or ""
                    )

                elif elem.tag == 'programme':
                    channel_id = elem.get('channel')
                    start_str = elem.get('start')
                    stop_str = elem.get('stop')

                    if not channel_id or not start_str or not stop_str:
                        elem.clear()
                        continue

                    start_dt = self.parse_xmltv_date(start_str)
                    stop_dt = self.parse_xmltv_date(stop_str)

                    if not start_dt or not stop_dt:
                        elem.clear()
                        continue

                    # Filter old programs
                    if stop_dt < now:
                        elem.clear()
                        continue

                    # Filter far future programs
                    if start_dt > cutoff:
                        elem.clear()
                        continue

                    title_elem = elem.find('title')
                    title = title_elem.text if title_elem is not None else "N/A"

                    desc_elem = elem.find('desc')
                    desc = desc_elem.text if desc_elem is not None else ""

                    prog = Program(
                        channel_id=channel_id,
                        start=start_dt,
                        stop=stop_dt,
                        title=title,
                        desc=desc or ""
                    )

                    if channel_id not in programs:
                        programs[channel_id] = []
                    programs[channel_id].append(prog)

                # Clear element to free memory
                elem.clear()

        except Exception as e:
            logging.error("XML parsing error: {}".format(e))

        logging.info(
            "Parsed {} channels, {} programs".format(
                len(channels), sum(
                    len(p) for p in programs.values())))
        return channels, programs


class EPGManager:
    """Main EPG management class combining all components."""

    DEFAULT_SOURCES = [
        EPGSource(
            name="Italy",
            url="https://epgshare01.online/epgshare01/epg_ripper_IT1.xml.gz",
            backup_url="https://iptv-epg.org/files/epg-it.xml.gz",
            priority=0,
            enabled=True,
            country_code="it"
        ),
        EPGSource(
            name="France",
            url="https://epgshare01.online/epgshare01/epg_ripper_FR1.xml.gz",
            priority=1,
            enabled=True,
            country_code="fr"
        ),
        EPGSource(
            name="Germany",
            url="https://epgshare01.online/epgshare01/epg_ripper_DE1.xml.gz",
            priority=1,
            enabled=True,
            country_code="de"
        ),
        EPGSource(
            name="Spain",
            url="https://epgshare01.online/epgshare01/epg_ripper_ES1.xml.gz",
            priority=1,
            enabled=True,
            country_code="es"
        ),
        EPGSource(
            name="United Kingdom",
            url="https://epgshare01.online/epgshare01/epg_ripper_UK1.xml.gz",
            priority=1,
            enabled=True,
            country_code="gb"
        ),
        EPGSource(
            name="Portugal",
            url="https://epgshare01.online/epgshare01/epg_ripper_PT1.xml.gz",
            priority=1,
            enabled=True,
            country_code="pt"
        ),
        EPGSource(
            name="Netherlands",
            url="https://epgshare01.online/epgshare01/epg_ripper_NL1.xml.gz",
            priority=1,
            enabled=True,
            country_code="nl"
        ),
        EPGSource(
            name="Belgium",
            url="https://epgshare01.online/epgshare01/epg_ripper_BE2.xml.gz",
            priority=1,
            enabled=True,
            country_code="be"
        ),
        EPGSource(
            name="Austria",
            url="https://epgshare01.online/epgshare01/epg_ripper_AT1.xml.gz",
            priority=1,
            enabled=True,
            country_code="at"
        ),
        EPGSource(
            name="Switzerland",
            url="https://epgshare01.online/epgshare01/epg_ripper_CH1.xml.gz",
            priority=1,
            enabled=True,
            country_code="ch"
        ),
        EPGSource(
            name="Poland",
            url="https://epgshare01.online/epgshare01/epg_ripper_PL1.xml.gz",
            priority=1,
            enabled=True,
            country_code="pl"
        ),
        EPGSource(
            name="Romania",
            url="https://epgshare01.online/epgshare01/epg_ripper_RO1.xml.gz",
            priority=1,
            enabled=True,
            country_code="ro"
        ),
        EPGSource(
            name="Albania",
            url="https://epgshare01.online/epgshare01/epg_ripper_AL1.xml.gz",
            priority=1,
            enabled=True,
            country_code="al"
        ),
        EPGSource(
            name="Bulgaria",
            url="https://epgshare01.online/epgshare01/epg_ripper_BG1.xml.gz",
            priority=1,
            enabled=True,
            country_code="bg"
        ),
        EPGSource(
            name="Croatia",
            url="https://epgshare01.online/epgshare01/epg_ripper_HR1.xml.gz",
            priority=1,
            enabled=True,
            country_code="hr"
        ),
        EPGSource(
            name="Serbia",
            url="https://epgshare01.online/epgshare01/epg_ripper_RS1.xml.gz",
            priority=1,
            enabled=True,
            country_code="rs"
        ),
        EPGSource(
            name="Bosnia",
            url="https://epgshare01.online/epgshare01/epg_ripper_BA1.xml.gz",
            priority=1,
            enabled=True,
            country_code="ba"
        ),
        EPGSource(
            name="Czech Republic",
            url="https://epgshare01.online/epgshare01/epg_ripper_CZ1.xml.gz",
            priority=1,
            enabled=True,
            country_code="cz"
        ),
        EPGSource(
            name="Slovakia",
            url="https://epgshare01.online/epgshare01/epg_ripper_SK1.xml.gz",
            priority=1,
            enabled=True,
            country_code="sk"
        ),
        EPGSource(
            name="Hungary",
            url="https://epgshare01.online/epgshare01/epg_ripper_HU1.xml.gz",
            priority=1,
            enabled=True,
            country_code="hu"
        ),
        EPGSource(
            name="Greece",
            url="https://epgshare01.online/epgshare01/epg_ripper_GR1.xml.gz",
            priority=1,
            enabled=True,
            country_code="gr"
        ),
        EPGSource(
            name="Turkey",
            url="https://epgshare01.online/epgshare01/epg_ripper_TR1.xml.gz",
            priority=1,
            enabled=True,
            country_code="tr"
        ),
        EPGSource(
            name="Denmark",
            url="https://epgshare01.online/epgshare01/epg_ripper_DK1.xml.gz",
            priority=1,
            enabled=True,
            country_code="dk"
        ),
        EPGSource(
            name="Sweden",
            url="https://epgshare01.online/epgshare01/epg_ripper_SE1.xml.gz",
            priority=1,
            enabled=True,
            country_code="se"
        ),
        EPGSource(
            name="Norway",
            url="https://epgshare01.online/epgshare01/epg_ripper_NO1.xml.gz",
            priority=1,
            enabled=True,
            country_code="no"
        ),
        EPGSource(
            name="Finland",
            url="https://epgshare01.online/epgshare01/epg_ripper_FI1.xml.gz",
            priority=1,
            enabled=True,
            country_code="fi"
        ),
        EPGSource(
            name="Russia",
            url="https://epgshare01.online/epgshare01/epg_ripper_viva-russia.ru.xml.gz",
            priority=1,
            enabled=True,
            country_code="ru"
        ),
        EPGSource(
            name="USA",
            url="https://epgshare01.online/epgshare01/epg_ripper_US2.xml.gz",
            priority=1,
            enabled=True,
            country_code="us"
        ),
        EPGSource(
            name="Canada",
            url="https://epgshare01.online/epgshare01/epg_ripper_CA2.xml.gz",
            priority=1,
            enabled=True,
            country_code="ca"
        ),
        EPGSource(
            name="Australia",
            url="https://epgshare01.online/epgshare01/epg_ripper_AU1.xml.gz",
            priority=1,
            enabled=True,
            country_code="au"
        ),
        EPGSource(
            name="Japan",
            url="https://epgshare01.online/epgshare01/epg_ripper_JP1.xml.gz",
            priority=1,
            enabled=True,
            country_code="jp"
        ),
        EPGSource(
            name="India",
            url="https://epgshare01.online/epgshare01/epg_ripper_IN1.xml.gz",
            priority=1,
            enabled=True,
            country_code="in"
        ),
        EPGSource(
            name="Brazil",
            url="https://epgshare01.online/epgshare01/epg_ripper_BR1.xml.gz",
            priority=1,
            enabled=True,
            country_code="br"
        ),
        EPGSource(
            name="Mexico",
            url="https://epgshare01.online/epgshare01/epg_ripper_MX1.xml.gz",
            priority=1,
            enabled=True,
            country_code="mx"
        ),
    ]

    def __init__(self,
                 cache_dir: Optional[Path] = None,
                 cache_ttl_hours: int = 12,
                 user_agent: str = "VAVOO/2.6",
                 sources: Optional[List[EPGSource]] = None):
        self.cache = EPGCache(cache_dir, cache_ttl_hours)
        self.downloader = EPGDownloader(user_agent)
        self.parser = EPGParser()
        self.sources = sources if sources is not None else self.DEFAULT_SOURCES

        # In-memory storage
        self.channels: Dict[str, ChannelInfo] = {}
        self.programs: Dict[str, List[Program]] = {}
        self.name_to_id: Dict[str, str] = {}  # normalized name -> channel id

    def load_all(self, force_refresh: bool = False) -> bool:
        """Load all EPG sources.

        Args:
            force_refresh: If True, ignore cache and download fresh.

        Returns:
            True if at least one source loaded successfully.
        """
        success = False

        for source in self.sources:
            if not source.enabled:
                continue

            if self._load_source(source, force_refresh):
                success = True

        self._build_name_index()
        return success

    def _load_source(self, source, force_refresh):
        """Load a single EPG source."""
        xml_content = None

        # Try cache first
        if not force_refresh:
            xml_content = self.cache.get_cached(source.name)
            if xml_content:
                logging.info("Using cached EPG for {}".format(source.name))

        # Download if not cached
        if xml_content is None:
            gz_content = self.downloader.download(source)
            if gz_content:
                xml_content = self.downloader.decompress(
                    gz_content, source.url)
                if xml_content:
                    self.cache.save(source.name, xml_content)

        if xml_content is None:
            logging.error("Failed to load EPG for {}".format(source.name))
            return False

        # Parse and merge
        channels, programs = self.parser.parse(
            xml_content, source.name, country_code=source.country_code)

        # Merge into main storage
        self.channels.update(channels)
        for ch_id, progs in programs.items():
            if ch_id not in self.programs:
                self.programs[ch_id] = []
            self.programs[ch_id].extend(progs)

        return True

    def _build_name_index(self):
        """Build index for name-based lookups."""
        self.name_to_id = {}
        for ch_id, info in self.channels.items():
            self.name_to_id[info.normalized_name] = ch_id

    def get_channel_by_name(self, name: str) -> Optional[ChannelInfo]:
        """Find channel by normalized name."""
        norm = self.parser.normalize_name(name)
        ch_id = self.name_to_id.get(norm)
        return self.channels.get(ch_id) if ch_id else None

    def get_current_program(self,
                            channel_id: str,
                            norm_name: Optional[str] = None) -> Tuple[Optional[str],
                                                                      Optional[str],
                                                                      Optional[datetime],
                                                                      Optional[datetime]]:
        """Get current program for a channel.

        Returns:
            Tuple of (title, description, start, stop)
        """
        now = datetime.now(timezone.utc)

        # Try to find channel ID from name if not found
        if channel_id not in self.programs and norm_name:
            channel_id = self.name_to_id.get(norm_name, channel_id)

        if channel_id not in self.programs:
            return None, None, None, None

        for prog in self.programs[channel_id]:
            if prog.start <= now <= prog.stop:
                return prog.title, prog.desc, prog.start, prog.stop

        return "No Info Available", "", None, None

    def get_upcoming_programs(
            self,
            channel_id: str,
            count: int = 5) -> List[Program]:
        """Get upcoming programs for a channel."""
        now = datetime.now(timezone.utc)

        if channel_id not in self.programs:
            return []

        upcoming = [p for p in self.programs[channel_id] if p.start > now]
        upcoming.sort(key=lambda p: p.start)

        return upcoming[:count]

    def clear_cache(self):
        """Clear all cached EPG data."""
        self.cache.clear()


# Convenience function for backward compatibility
def load_epg_data(user_agent: str = "VAVOO/2.6",
                  cache_dir: Optional[Path] = None,
                  force_refresh: bool = False) -> EPGManager:
    """Load EPG data and return manager instance."""
    manager = EPGManager(cache_dir=cache_dir, user_agent=user_agent)
    manager.load_all(force_refresh)
    return manager


if __name__ == "__main__":
    # Test the module
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )

    manager = EPGManager()
    if manager.load_all():
        print("Loaded {} channels".format(len(manager.channels)))
        print("Loaded programs for {} channels".format(len(manager.programs)))

        # Test lookup
        rai1 = manager.get_channel_by_name("Rai 1")
        if rai1:
            print("Found RAI 1: {}".format(rai1.display_name))
            title, desc, start, stop = manager.get_current_program(rai1.id)
            print("Current program: {}".format(title))

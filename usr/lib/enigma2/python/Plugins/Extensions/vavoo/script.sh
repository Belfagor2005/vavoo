#!/bin/bash
#######################################################################################
#######################################################################################
### https://www.digital-eliteboard.com/threads/autoscript-vavoo-auf-e2.513335/
### On an idea of Clever999 modified by Demosat 09.02.2023
#######################################################################################
#######################################################################################
echo -e "\033[32m###Vavoo-Script on an idea of Clever999 modified by Demosat\033[0m"
sleep 2
echo -e "\033[32m###### thx to MasterX, giniman and Oyster for the authkey\033[0m"
sleep 2
echo -e "\033[32m###more info https://www.digital-eliteboard.com/threads/autoscript-vavoo-auf-e2.513335/\033[0m"
sleep 2
########################################################################################
########################################################################################
########################################################################################
echo "start install..."


###Paketprüfung
echo pruefe curl
PAKET=curl
if [[ -f $(which $PAKET 2>/dev/null) ]]
    then
    echo -e "\033[32m$PAKET ist bereits installiert...\033[0m"

    else
    echo -e "\033[33m$PAKET wird installiert...\033[0m"
        opkg update && opkg install $PAKET
fi
sleep 1
vec=$(shuf -n 1 /home/vavookeys)
authkey="$(curl -k --location --request POST 'https://www.vavoo.tv/api/box/ping2' --header 'Content-Type: application/json' --data "{\"vec\": \"$vec\"}" | sed 's#^.*"signed":"##' | sed "s#\"}}##g" | sed 's/".*//')"
curl -k "https://www2.vavoo.to/live2/index?countries=all&output=json" > vavoo

echo "#EXTM3U" > index
cat vavoo | sed 's/\(}\),/\1}\n,/g' | sed 's/"url":"/"url":\n/g' | sed 's#,{\"group\":#\#EXTINF:-1 group-title=#g' | sed 's#,\"logo\":\"\",\"name\":#,#g' | sed 's/\"}.*//' | sed 's/\",\"tvg.*//' | sed 's#\",\"#\",#g'  >> index 
mv index index.m3u
for country in Italy; do
    cat index.m3u | grep -E -A1 =\"$country > $country.m3u
    # file m3u for vlc
    echo erstelle $country.m3u...
    echo "#EXTM3U" > vavoo-$country.m3u
    cat $country.m3u | sed "s#.ts#.ts?n=1\&b=5\&vavoo_auth="$authkey"#g" | sed '/^#EXTINF/a#EXTVLCOPT:http-user-agent=VAVOO/2.6' >> vavoo-$country.m3u
    # file for enigma2
    echo erstelle vavoo-$country bouquets...
    echo "#NAME Vavoo-"$country > /etc/enigma2/userbouquet.vavoo-$country.tv
    cat $country.m3u | sed "s#.ts#.ts?n=1\&b=5\&vavoo_auth="$authkey"\#User-Agent=VAVOO/2.6#g" | sed '/^#EXTINF/{h;d}; /^http/G' | sed 's#,#,\#DESCRIPTION #g' | sed 's#^.*,##' | sed 's#:#%3a#g' | sed 's#http#\#SERVICE 4097:0:0:0:0:0:0:0:0:0:http#g' |  sed '/--/d; s/#DESCRIPTION/@#DESCRIPTION/g' | sed '$!N;s/\n/ /' | sort -k 4 | sed 's/@/\n/g; s/@//g' >> /etc/enigma2/userbouquet.vavoo-$country.tv
if cat /etc/enigma2/bouquets.tv  | grep vavoo-$country > /dev/null 2>&1
    then
    echo -e Entry bouquets.tv $country available > /dev/null 2>&1
    else
    echo -e Entry bouquets.tv $country is missing > /dev/null 2>&1
    echo "#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"userbouquet.vavoo-$country.tv\" ORDER BY bouquet" >> /etc/enigma2/bouquets.tv
fi

# rm -rf $country.m3u
done

rm index*
####bouquets.tv SID pruefen###
if
    cat /etc/enigma2/bouquets.tv  | grep vavoosid > /dev/null 2>&1
    then
    echo -e Eintrag bouquets.tv vorhanden > /dev/null 2>&1
    else
    echo -e Eintrag bouquets.tv fehlt > /dev/null 2>&1
    echo "#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"userbouquet.vavoosid.tv\" ORDER BY bouquet" >> /etc/enigma2/bouquets.tv
fi

####pfad zur userbouquet sid###
echo erstelle SID Germany
pfad=/etc/enigma2/userbouquet.vavoo-Germany.tv
###sids bearbeiten####
echo "#NAME vavooSID" > e3
echo "#SERVICE 1:64:1:2:0:0SID:0:0:0:0:http%3a//egal.de:##### FTA #####" >> e3
echo "#DESCRIPTION ##### FTA #####" >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Das Erste" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:283D:3FB:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION DasErste" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:283D:3FB:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION ARD HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:283D:3FB:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION ARD FHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:283D:3FB:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION ZDF HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:2B66:3F3:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION ZDF FHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:2B66:3F3:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION ZDF RAW" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:2B66:3F3:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION SWR HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:283F:3FB:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION SWR FHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:283F:3FB:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION SWR RAW" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:283F:3FB:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION SWR BW HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:283F:3FB:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION SWR BW FHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:283F:3FB:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION SWR BW RAW" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:283F:3FB:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION SRF 1" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:4331:300C:13E:820000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION SRF1" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:4331:300C:13E:820000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION SRF 2" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:4332:300C:13E:820000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION SRF2" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:4332:300C:13E:820000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION SRFzwei" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:4332:300C:13E:820000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION SRF zwei" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:4332:300C:13E:820000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION SRF info" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:4335:300C:13E:820000:0:0:0:#g' >> e3 
    cat $pfad | grep -B 1 -i "DESCRIPTION SRFinfo" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:4335:300C:13E:820000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION ORF 1" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:132F:3EF:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION ORF1" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:132F:3EF:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION ORFeins" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:132F:3EF:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION ORF eins" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:132F:3EF:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION ORF 2" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:1330:3EF:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION ORF2" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:1330:3EF:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION ORF 3" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:33FC:3ED:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION ORF3" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:33FC:3ED:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Orf III" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:33FC:3ED:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sat.1 HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF74:3F9:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sat.1 RAW" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF74:3F9:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sat.1 FHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF74:3F9:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sat1 HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF74:3F9:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sat1 FHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF74:3F9:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sat1 RAW" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF74:3F9:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION RTL HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF10:421:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION RTL FHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF10:421:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION RTL RAW" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF10:421:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION RTL CH HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF10:421:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION RTL2 HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF15:421:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION RTL2 RAW" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF15:421:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION RTL2 FHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF15:421:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION RTL 2 HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF15:421:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION RTL 2 RAW" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF15:421:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION RTL 2 FHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF15:421:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION RTLzwei HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF15:421:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION RTLzwei FHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF15:421:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION RTLzwei RAW" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF15:421:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION RTLII HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF15:421:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION RTLII FHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF15:421:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION RTLII RAW" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF15:421:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION ProSieben HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF75:3F9:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION ProSieben FHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF75:3F9:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION ProSieben RAW" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF75:3F9:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Pro Sieben HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF75:3F9:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Pro Sieben FHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF75:3F9:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Pro Sieben RAW" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF75:3F9:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Pro7 HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF75:3F9:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Pro7 FHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF75:3F9:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Pro7 RAW" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF75:3F9:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Pro 7 HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF75:3F9:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Pro 7 FHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF75:3F9:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Pro 7 RAW" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF75:3F9:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION kabel eins HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF76:3F9:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION kabel eins FHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF76:3F9:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION kabel eins RAW" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF76:3F9:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION kabeleins HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF76:3F9:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION kabeleins FHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF76:3F9:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION kabeleins RAW" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF76:3F9:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION kabel1 HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF76:3F9:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION kabel1 FHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF76:3F9:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION kabel1 RAW" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF76:3F9:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION kabel 1 HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF76:3F9:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION kabel 1 FHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF76:3F9:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION kabel 1 RAW" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF76:3F9:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Vox HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#1:0:1:2F1C:441:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Vox FHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#1:0:1:2F1C:441:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Vox RAW" | sed 's#4097:0:0:0:0:0:0:0:0:0:#1:0:1:2F1C:441:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Nitro" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:2EAF:411:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION sixx" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF77:3F9:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION DMAX" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:151A:455:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION PHOENIX" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:285B:401:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION ServusTV" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:1332:3EF:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Servus TV" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:1332:3EF:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION ZDF:neo" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:2B7A:3F3:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION ZDFneo" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:2B7A:3F3:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION ZDF neo" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:2B7A:3F3:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION ZDF_neo" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:2B7A:3F3:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION ZDFinfo" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:2BA2:3F2:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION ZDF info" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:2BA2:3F2:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION arte" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:283E:3FB:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION 3sat" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:2B8E:3F2:1:C00000:0:0:0:#g' >> e3
echo "#SERVICE 1:64:1:2:0:0:0:0:0:0:http%3a//egal.de:##### Unterhaltung #####" >> e3
echo "#DESCRIPTION ##### Unterhaltung #####" >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Cinema Premieren HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:83:6:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Cinema Premieren FHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:83:6:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Cinema Premieren RAW" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:83:6:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Cinema HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:83:6:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Cinema FHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:83:6:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Cinema RAW" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:83:6:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Cinema Premieren +24" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:87:B:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Cinema Premieren 24" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:87:B:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Cinema Premieren24" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:87:B:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Cinema Premieren+24" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:87:B:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Cinema Premieren 24" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:87:B:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Cinema +24" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:87:B:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Cinema 24" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:87:B:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Cinema+24" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:87:B:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Cinema24" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:87:B:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Cinema Best Of" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:6B:C:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Best Of" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:6B:C:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Cinema Action" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:74:3:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Action" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:74:3:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Cinema Spezial" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:6F:D:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Cinema Special" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:6F:D:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Spezial" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:6F:D:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Special" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:6F:D:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Cinema Thriller" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:B:4:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Thriller" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:B:4:85:C00000:0:0:0:#g' >> e3    
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Cinema Family" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:8B:2:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Family" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:8B:2:85:C00000:0:0:0:#g' >> e3    
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Krimi" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:17:4:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Atlantic" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:6E:D:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky 1" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:93:2:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky One" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:93:2:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Replay" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:7C:C:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Comedy" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:E:2:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Crime" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:D:6:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION HEIMAT" | sed 's#4097:0:0:0:0:0:0:0:0:0:#1:0:16:16:2:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Romance TV" | sed 's#4097:0:0:0:0:0:0:0:0:0:#1:0:16:206:2:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION SYFY" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:7E:C:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION 13th Street" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:7F:D:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION SONY AXN" | sed 's#4097:0:0:0:0:0:0:0:0:0:#1:0:16:101D:451:35:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Universal TV" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:65:8:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Warner TV Film" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:8C:4:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Warner TV Serie" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:7B:8:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Warner TV Comedy" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:88:B:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Warner Film" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:8C:4:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Warner Serie" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:7B:8:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Warner Comedy" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:88:B:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION TNT Film" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:8C:4:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION TNT Serie" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:7B:8:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION TNT Comedy" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:88:B:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION KABEL 1 CLASSICS" | sed 's#4097:0:0:0:0:0:0:0:0:0:#1:0:16:14C2:407:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION kabeleinsclassics" | sed 's#4097:0:0:0:0:0:0:0:0:0:#1:0:16:14C2:407:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION KINOWELT TV" | sed 's#4097:0:0:0:0:0:0:0:0:0:#1:0:16:196:B:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Anixe" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:526C:41D:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Pro7 MAXX" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF78:3F9:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION ProSieben MAXX" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF78:3F9:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION RTL Crime" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:8C:9:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION ProSieben Fun" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:B54:1BBC:9C:5A0000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Pro Sieben Fun" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:B54:1BBC:9C:5A0000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Pro7 Fun" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:B54:1BBC:9C:5A0000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Pro 7 Fun" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:B54:1BBC:9C:5A0000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION RTL Living" | sed 's#4097:0:0:0:0:0:0:0:0:0:#1:0:1:2EC3:411:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION RTL Passion" | sed 's#4097:0:0:0:0:0:0:0:0:0:#1:0:16:1D:4:85:C00000:0:0:0:#g' >> e3
echo "#SERVICE 1:64:1:2:0:0:0:0:0:0:http%3a//egal.de:##### Doku #####" >> e3
echo "#DESCRIPTION ##### Doku #####" >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Discovery" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:82:6:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION NatGeo HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:70:D:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION NatGeo FHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:70:D:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION NatGeo RAW" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:70:D:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION National Geographic HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:70:D:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION National Geographic FHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:70:D:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION National Geographic RAW" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:70:D:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Nat Geo Wild" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:76:6:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION National Geographic Wild" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:76:6:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION HISTORY" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:71:B:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Spiegel Geschichte" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:89:10:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Spiegel TV Wissen" | sed 's#4097:0:0:0:0:0:0:0:0:0:#1:0:16:31:D:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Curiosity Channel HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#1:0:16:31:D:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Documentaries" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:10:3:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Nature" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:F:2:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Animal Planet" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:4DA:C:1:FFFF0000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Planet HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:AC48:1AF:270F:FFFF0000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Planet FHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:AC48:1AF:270F:FFFF0000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Planet RAW" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:AC48:1AF:270F:FFFF0000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION BILD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:2775:409:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "Welt HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#1:0:1:445F:453:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "Welt FHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#1:0:1:445F:453:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "Welt RAW" | sed 's#4097:0:0:0:0:0:0:0:0:0:#1:0:1:445F:453:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "Geo TV" | sed 's#1:0:0:0:0:0:0:0:0:0:#4097:0:19:A092:19B:270F:FFFF0000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "GeoTV" | sed 's#1:0:0:0:0:0:0:0:0:0:#4097:0:19:A092:19B:270F:FFFF0000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION NTV" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF14:421:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION N-TV H" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:EF14:421:1:C00000:0:0:0:#g' >> e3
echo "#SERVICE 1:64:1:2:0:0:0:0:0:0:http%3a//egal.de:##### Kids #####" >> e3
echo "#DESCRIPTION ##### Kids #####" >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Comedy Central" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:6FEC:436:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Disney Junior" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:8A:3:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Kika HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:2B98:3F2:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Super RTL HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:2E9B:411:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION DISNEY CHANNEL HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:157C:41F:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION DISNEY CHANNEL FHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:157C:41F:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION DISNEY CHANNEL RAW" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:157C:41F:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION DISNEY HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:157C:41F:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION DISNEY FHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:157C:41F:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION DISNEY RHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:157C:41F:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION nick/MTV+" | sed 's#4097:0:0:0:0:0:0:0:0:0:#1:0:1:7008:436:1:C00000:0:0:0:#g' >> e3
echo "#SERVICE 1:64:1:2:0:0:0:0:0:0:http%3a//egal.de:##### Musik #####" >> e3
echo "#DESCRIPTION ##### Musik #####" >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION DELUXE MUSIC" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:157F:41F:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION MTV HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:2777:409:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION MTV Live" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:4E3D:802:600:FFFF0000:0:0:0:#g' >> e3
echo "#SERVICE 1:64:1:2:0:0:0:0:0:0:http%3a//egal.de:##### Sport #####" >> e3
echo "#DESCRIPTION ##### Sport #####" >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION MotorVision" | sed 's#4097:0:0:0:0:0:0:0:0:0:#1:0:16:A8:B:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Auto Motor und Sport" | sed 's#1:0:0:0:0:0:0:0:0:0:#4097:0:19:17D7:C91:3:EB0000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Auto Motor Sport" | sed 's#1:0:0:0:0:0:0:0:0:0:#4097:0:19:17D7:C91:3:EB0000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION ORF Sport" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:33FD:3ED:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION ORFSport" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:33FD:3ED:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sport1 HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:1581:41F:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sport 1 HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:1581:41F:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sport1+" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:10CD:418:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sport 1+" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:10CD:418:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Eurosport 1" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:30D6:413:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Eurosport1" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:30D6:413:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Eurosport 2" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:6D:B:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Eurosport2" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:6D:B:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION DAZN 1" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:84:8:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION DAZN1" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:84:8:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION DAZN 2" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:7A:10:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION DAZN2" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:7A:10:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Premier League" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:91:4:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Sport F1" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:11:3:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Sport Tennis" | sed 's#4097:0:0:0:0:0:0:0:0:0:#1:0:16:DE:2:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Sport Golf" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:90:D:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Sport Mix" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:8D:2:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Sport Top Event" | sed 's#4097:0:0:0:0:0:0:0:0:0:#1:0:16:DD:4:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Sport 1" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:10C:6:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Sport 2" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:116:2:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Sport 3" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:120:C:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Sport 4" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:12A:8:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Sport 5" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:134:4:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Sport 6" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:13E:3:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Sport 7" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:148:3:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Sport 8" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:152:10:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Sport 9" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:102:B:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Sport Bundesliga HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#1:0:16:DF:4:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Sport Bundesliga FHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#1:0:16:DF:4:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Sport Bundesliga RAW" | sed 's#4097:0:0:0:0:0:0:0:0:0:#1:0:16:DF:4:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Bundesliga HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#1:0:16:DF:4:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Bundesliga FHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#1:0:16:DF:4:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Bundesliga RAW" | sed 's#4097:0:0:0:0:0:0:0:0:0:#1:0:16:DF:4:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Sport Bundesliga 1 HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:10B:6:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Sport Bundesliga 1 FHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:10B:6:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Sport Bundesliga 1 RAW" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:10B:6:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Bundesliga 1 HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:10B:6:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Bundesliga 1 FHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:10B:6:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Bundesliga 1 RAW" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:10B:6:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Sport Bundesliga 1" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:10B:6:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Bundesliga 1" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:10B:6:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Sport Bundesliga 2" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:115:2:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Bundesliga 2" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:115:2:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Sport Bundesliga 3" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:11F:C:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Bundesliga 3" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:11F:C:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Bundesliga 4" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:129:8:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Bundesliga 5" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:133:4:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Bundesliga 6" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:13D:3:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Bundesliga 7" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:147:3:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Bundesliga 8" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:151:10:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Bundesliga 9" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:101:B:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Sport Austria HD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:8F:8:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Sport Austria 1" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:8F:8:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Sport Austria 2" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:149:8:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Sport Austria 3" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:153:8:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Sport Austria 4" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:153:2:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Sport Austria 5" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:146:3:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Sport Austria 6" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:156:10:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Sport Austria 7" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:105:B:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Sport UHD" | sed 's#4097:0:0:0:0:0:0:0:0:0:#1:0:1F:229:10:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Sky Sport News" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:6C:C:85:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION SPORTDIGITAL FUSSBALL" | sed 's#4097:0:0:0:0:0:0:0:0:0:#4097:0:19:10CC:418:1:C00000:0:0:0:#g' >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Magenta " >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Telekom " >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION RTL+ " >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION DAZN " >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Max Kino " >> e3
    cat $pfad | grep -B 1 -i "DESCRIPTION Eagle " >> e3
mv e3 /etc/enigma2/userbouquet.vavoosid.tv
###Playlist neu laden in ###
echo reload bouquets...
wget -q -qO - http://127.0.0.1/web/servicelistreload?mode=0 > /dev/null 2>&1
sleep 1
###Pruefen Cron###
echo Pruefe cron...
sleep 1
if cat /etc/cron/crontabs/root | grep /home/vavoosid.sh > /dev/null 2>&1
    then 
    echo -e "\033[32mCron vorhanden\033[0m"
    else
    echo -e "\033[33mCron Update\033[0m"
    echo "*/10 * * * * /home/vavoosid.sh" >> /etc/cron/crontabs/root
    echo "@reboot /home/vavoosid.sh" >> /etc/cron/crontabs/root
fi
sleep 1
echo all finished.. happy viewing
exit 0
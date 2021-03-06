import json
import re
from time import sleep

import requests as req
from path import Path
from selenium import webdriver

WEB = True


class Ope:
    def __init__(self):
        self.city_code = 'https://hotels.ctrip.com/Domestic/Tool/AjaxDestination.aspx'
        self.sub_city_code = 'https://hotels.ctrip.com/Domestic/Tool/AjaxGetHotKeyword.aspx'
        self.hotel_num = 'https://hotels.ctrip.com/Domestic/Tool/AjaxHotelList.aspx'

    @staticmethod
    def parser_res(res):
        if '验证访问' in res.text:
            print('访问次数过多')
            if WEB:
                driver = webdriver.Chrome()
                driver.get(res.url)
                sleep(10)
            else:
                sleep(30)
            return False
        return True

    def get_city_code(self, city):
        res = req.get(self.city_code, params={'keyword': city, 'from': 'domestic'}, timeout=5)
        while not self.parser_res(res):
            res = req.get(self.city_code, params={'keyword': city, 'from': 'domestic'}, timeout=5)
        return re.findall(f'"key":"{city}","data":"@[a-z]+\'*[a-z]+\|{city}\|(\d+)\|', res.text, re.I)

    def get_sub_city_code(self, city_code):
        res = req.get(self.sub_city_code, params={'cityid': city_code}, timeout=5)
        while not self.parser_res(res):
            res = req.get(self.sub_city_code, params={'cityid': city_code}, timeout=5)
        res = res.text
        if 'cQuery.jsonpResponse={};cQuery.jsonpResponse.suggestion=null' in res:
            return []
        elif not res:
            return []
        res = res[res.find('suggestion={') + len('suggestion='):]
        if r"\'" in res:
            res = res.replace(r"\'", r"\\'")
        try:
            res = json.loads(res)
        except:
            print(res)
        # res = json.loads(res)
        return res.get('locationId', {'data': []})['data'] + res.get('subCity', {'data': []})['data']

    @staticmethod
    def _get_pars(city_code, sub_city_code):
        data = '''
            RoomGuestCount:1,1,0
            txtkeyword:
            Resource:
            Room:
            Paymentterm:
            BRev:
            Minstate:
            PromoteType:
            PromoteDate:
            operationtype:NEWHOTELORDER
            PromoteStartDate:
            PromoteEndDate:
            OrderID:
            RoomNum:
            IsOnlyAirHotel:F
            cityId:7
            positionArea:Location
            hotelposition:
            keyword:
            hotelId:
            htlPageView:0
            hotelType:F
            hasPKGHotel:F
            requestTravelMoney:F
            isusergiftcard:F
            useFG:F
            HotelEquipment:
            hotelBrandId:
            promotion:F
            prepay:F
            IsCanReserve:F
            OrderBy:99
            OrderType:
            k1:
            k2:
            CorpPayType:
            viewType:
            DealSale:
            ulogin:
            psid:
            isfromlist:T
            ubt_price_key:htl_search_result_promotion
            showwindow:
            defaultcoupon:
            isHuaZhu:False
            hotelPriceLow:
            unBookHotelTraceCode:
            showTipFlg:
            traceAdContextId:
            allianceid:0
            sid:0
            pyramidHotels:
            markType:3
            type:
            brand:
            group:
            feature:
            equip:
            bed:
            breakfast:
            other:
            star:
            price:
            a:0
            keywordLat:
            keywordLon:
            contrast:0
            PaymentType:
            CtripService:
            promotionf:
            allpoint:
            zone:
            sl:
            l:
            s:
            '''
        res = {}
        for i in data.split('\n'):
            if i.strip():
                key, value = i.strip().split(':')
                res[key] = value.strip()
        res['cityId'] = city_code

        if isinstance(sub_city_code, dict):
            if 'Location' == sub_city_code['type']:
                res['location'] = sub_city_code['id']
            else:
                res['cityId'] = sub_city_code['id']
        return res

    @staticmethod
    def _parser_num(res):
        try:
            return res.json()['hotelAmount']
        except:
            return re.findall('"hotelAmount":(\d*),', res.text)[0]

    def _get_all_hotel_num(self, city_code, sub_city_code):
        res = self._get_pars(city_code, sub_city_code)
        res = req.post(self.hotel_num, res, timeout=5)
        while not self.parser_res(res):
            res = req.post(self.hotel_num, res, timeout=5)
        return self._parser_num(res)

    def _get_hotel_num_by_price(self, city_code, sub_city_code):
        res = self._get_pars(city_code, sub_city_code)
        res['price'] = 'v0v200'
        res = req.post(self.hotel_num, res, timeout=5)
        while not self.parser_res(res):
            res = req.post(self.hotel_num, res, timeout=5)
        return self._parser_num(res)

    def _get_hotel_num_by_star(self, city_code, sub_city_code):
        res = self._get_pars(city_code, sub_city_code)
        res['star'] = '4,5'
        res = req.post(self.hotel_num, res, timeout=5)
        while not self.parser_res(res):
            res = req.post(self.hotel_num, res)
        return self._parser_num(res)

    def get_hotel_num(self, city_code, sub_city_code):
        all_num = self._get_all_hotel_num(city_code, sub_city_code)
        num_price = self._get_hotel_num_by_price(city_code, sub_city_code)
        num_star = self._get_hotel_num_by_star(city_code, sub_city_code)
        return all_num, num_price, num_star


class XC(Ope):
    @property
    def get_all_city(self):
        return [i.strip() for i in Path('City').lines(encoding='utf-8') if i.strip()]

    @staticmethod
    def get_loads():
        if Path('Result.txt').exists():
            return [','.join(i.split(',')[:2]) for i in Path('Result.txt').lines(encoding='utf-8') if ',' in i]
        return []

    @staticmethod
    def dump(res):
        print(res)
        Path('Result.txt').write_text(','.join([str(i) for i in res]) + '\n', append=True, encoding='utf-8')

    def signal(self, city):
        city_code = self.get_city_code(city)
        sub_city_code = self.get_sub_city_code(city_code)
        for sub_city in sub_city_code:
            num = self.get_hotel_num(city_code, sub_city)
            res = [city, sub_city["name"]] + list(num)
            print(res)

    def run(self):
        loads = self.get_loads()
        for city in self.get_all_city:
            try:
                city_code = self.get_city_code(city)
                if not city_code:
                    continue
                sub_city_code = self.get_sub_city_code(city_code)
                if sub_city_code:
                    for sub_city in sub_city_code:
                        if f'{city},{sub_city["name"]}' not in loads:
                            num = self.get_hotel_num(city_code, sub_city)
                            res = [city, sub_city["name"]] + list(num)
                            self.dump(res)
                else:
                    if f'{city},{city}' not in loads:
                        num = self.get_hotel_num(city_code, city)
                        res = [city, city] + list(num)
                        self.dump(res)
            except Exception as e:
                print(e)


if __name__ == '__main__':
    xc = XC()
    xc.run()

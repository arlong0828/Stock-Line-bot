import twstock

class stockServices:
    async def get_realtime_price(stock_ids : list):
        twstock.__update_codes()
        try:
            for stock_id in stock_ids:
                stock = twstock.realtime.get(stock_id)
                if stock['success']:
                    return {
                        "name" : stock["info"]["name"],
                        "price" : stock["realtime"]["latest_trade_price"],
                        "status" : "success"
                    }
                return {"status" : "error" , "message" : "找不到該股票"}
        except Exception as e:
            return {"status" : "error" , "message" : str(e)}
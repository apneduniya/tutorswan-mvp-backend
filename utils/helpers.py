
def helpers_multiple(data) -> dict:
    external_order_data: dict = data
    for i in range(len(external_order_data)):
        external_order_data[i]["id"] = str(external_order_data[i]["_id"])
        del external_order_data[i]["_id"]
    # return {
    # "id": str(data["_id"]),
    # **external_order_data
    # }
    return external_order_data

def helpers_single(data) -> dict:
    external_order_data: dict = data
    external_order_data["id"] = str(external_order_data["_id"])
    del external_order_data["_id"]
    return external_order_data
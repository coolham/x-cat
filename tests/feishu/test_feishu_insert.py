import json

import lark_oapi as lark
from lark_oapi.api.bitable.v1 import *


def main():
    # 创建client
    # 使用 user_access_token 需开启 token 配置, 并在 request_option 中配置 token
    client = lark.Client.builder() \
        .enable_set_token(True) \
        .log_level(lark.LogLevel.DEBUG) \
        .build()

    # 构造请求对象
    request: CreateAppTableRecordRequest = CreateAppTableRecordRequest.builder() \
        .app_token("ZP1BbR6fqaCpDosf3gXc9OZhnJb") \
        .table_id("tblHKTdD3z2gHGNP") \
        .user_id_type("user_id") \
        .request_body(AppTableRecord.builder()
            .fields({"原始内容":"Hi222","数据类型":"TEXT","来源":"twitter"})
            .build()) \
        .build()

    # 发起请求
    option = lark.RequestOption.builder().user_access_token("u-d5pY4XK5p0Toik794MQtVvlhmgc11ll9Ma205hc22cTW").build()
    response: CreateAppTableRecordResponse = client.bitable.v1.app_table_record.create(request, option)

    # 处理失败返回
    if not response.success():
        lark.logger.error(
            f"client.bitable.v1.app_table_record.create failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}")
        return

    # 处理业务结果
    lark.logger.info(lark.JSON.marshal(response.data, indent=4))


if __name__ == "__main__":
    main()
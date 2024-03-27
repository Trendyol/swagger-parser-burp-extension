# SwaggerParser-BurpExtension

With this extension, you can parse Swagger Documents. You can view the parsed requests in the table and send them to Repeater, Intruder, Scanner.

## How to use

**1- Extension written in Python. That's why he works with Jython. We need to add the Jython jar file to Burp.**

![jython_install](https://github.com/bulutenes/SwaggerParser-BurpExtension/assets/150332295/1a657087-b9ed-4b3d-9fc3-352c15cf855c)


**2- After adding Jython to Burp, we can also add the Extension to Burp with the Extension's python file.**

![extension_install](https://github.com/bulutenes/SwaggerParser-BurpExtension/assets/150332295/3a178569-db57-420b-93ef-88be59b528c0)


**3- If the extension has been installed successfully, the "Swagger Parser" tab will be added. You can see the extension screen by clicking this tab.**

<img width="1792" alt="main_screen" src="https://github.com/Trendyol/swagger-parser-burp-extension/assets/150332295/810d11ed-b0a7-4648-a203-41cbb73ea7aa">

**Add New Swagger Document Panel:** This is the part where new Swagger Documents are added and edited.

<img width="1226" alt="add_new_doc" src="https://github.com/Trendyol/swagger-parser-burp-extension/assets/150332295/70c86d11-9900-4216-ab56-2def027ad3da">


**Request Detail Panel:** This is the section where the details of the parsed requests are displayed.

<img width="896" alt="request_detail" src="https://github.com/Trendyol/swagger-parser-burp-extension/assets/150332295/ce5a46d7-5782-4be3-9ec7-306f47dfb280">


**Custom Headers Panel:** Headers written below in this panel are added to all requests while parsing.

![custom_headers](https://github.com/bulutenes/SwaggerParser-BurpExtension/assets/150332295/b3e5e47a-b668-4d15-9b34-31e37f3637c8)


**Output Panel:** After the parse process is completed, all endpoints are listed in Markdown format.

![markdown_output](https://github.com/bulutenes/SwaggerParser-BurpExtension/assets/150332295/3ad59bc9-05f6-426e-b4be-71548c954217)


**Request History Panel:** After the parse process is completed, the requests are listed in the table and can be sent to the Repeater, Intruder, Scanner.

![send_to_feature](https://github.com/bulutenes/SwaggerParser-BurpExtension/assets/150332295/c8536ba6-ca77-40bc-9c4c-d3202f7ed2bd)


**4- We right-click on the Swagger Document request we want to parse and select the "Send to Swagger Parser" option and the parsing process begins.**

![send_to_swagger_parser](https://github.com/bulutenes/SwaggerParser-BurpExtension/assets/150332295/23acef55-b256-48f1-a3a5-3f5abec63345)

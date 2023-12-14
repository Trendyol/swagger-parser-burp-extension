from burp import IBurpExtender
from burp import IProxyListener
from burp import IContextMenuFactory
from java.util import ArrayList
from javax.swing import JMenuItem
from java.awt.event import MouseAdapter, MouseEvent

from javax.swing import (GroupLayout, JPanel, JComboBox, JCheckBox, JTextField, JLabel, JButton, JScrollPane, JTable, JPopupMenu, JTextPane)
from java.awt import (BorderLayout,Dimension, Toolkit)
from javax import swing
from burp import ITab
from javax.swing.table import (DefaultTableModel)

import threading
import json
import re
import random
import string


class SwaggerParser:
    def __init__(self, swagger_url, headers):
        self.swagger_url = swagger_url
        self.headers = headers


    def urlEncodingForEnum(self, param):
        return str(param).replace(" ","%20").replace(":", "%3A").replace("=","%3D").replace(",","%2C").replace(";","%3B")

    def randomValueGenerator(self, _param_name, _param_type, _schema):

        try:
            _temp_value = None
            _enum = _schema.get("enum")
            _default = _schema.get("default")
            _items = _schema.get("items")
            _format = _schema.get("format")

            if _param_type is None:
                _param_type = _schema.get("type")

            if _param_type == "string":

                _temp_value = ''.join(random.sample(string.ascii_lowercase, 8))

                if _default is not None:

                    if str(_default).strip() == "":
                        _default = "xxx"

                    _temp_value = _default
                elif _enum is not None and type(_enum) == list and len(_enum) > 0:
                    _temp_value = self.urlEncodingForEnum(_enum[0])
                elif _format is not None:
                    if _format in ["date", "date-time"]:
                        _temp_value = "01-01-2023"

            elif _param_type == "integer":

                _temp_value = random.randrange(100)
            elif _param_type == "number":

                _temp_value = random.randrange(100)
            elif _param_type == "boolean":

                _temp_value = True
            elif _param_type == "file":

                _temp_value = "RandomStringInput"#''.join(random.choices(string.ascii_lowercase, k=5))
            elif _param_type == "array":

                return [self.randomValueGenerator(None, None, _items)]
            elif len(_schema.keys()) > 0:

                _temp_obj = {}
                for _item_key in _schema:
                    _temp_obj[_item_key] = self.randomValueGenerator(None, None, _schema.get(_item_key))
                return _temp_obj
            else:
                "" #for debugging

            if _param_name is not None:
                return {_param_name: _temp_value}
            else:
                return _temp_value

        except Exception as e:
            print("randomValueGenerator error")
            print(e)

    def refObjectParser(self, _swagger_obj, _ref_value):

        _request_body_parameters_obj = _swagger_obj

        if "/" in _ref_value:
            _splitted_ref = str(_ref_value).split("/")
            for _ref_path in _splitted_ref:
                if _ref_path != "#" and _ref_path != "":
                    if _ref_path in _request_body_parameters_obj:

                        _request_body_parameters_obj = _request_body_parameters_obj.get(_ref_path)

                        if "properties" in _request_body_parameters_obj.keys() and _request_body_parameters_obj.get(
                                "type") == "object":
                            _request_body_parameters_obj = _request_body_parameters_obj["properties"]

                    else:
                        return {}

        return _request_body_parameters_obj

    def findAndParseAllRefs(self, _swagger_obj, _constat_swagger_obj):

        if type(_swagger_obj) == dict:
            for _key in _swagger_obj.keys():
                if _key == "$ref":
                    _temp_parsed_ref_obj = self.refObjectParser(_constat_swagger_obj, _swagger_obj.get(_key))

                    for _temp_key in _temp_parsed_ref_obj:
                        if _temp_key == "-":
                            continue
                        _swagger_obj[_temp_key] = _temp_parsed_ref_obj.get(_temp_key)
                    _swagger_obj.pop(_key)
                    break

                self.findAndParseAllRefs(_swagger_obj.get(_key), _constat_swagger_obj)
        elif type(_swagger_obj) == list:
            for _item in _swagger_obj:
                self.findAndParseAllRefs(_item, _constat_swagger_obj)
        else:
            "" #for debugging

        return _swagger_obj

    _all_keys = {}

    def generateRequest(self, _path, _method, _request_obj, _output_obj):

        if type(_request_obj) == dict:
            for _key in _request_obj.keys():
                self._all_keys[_key] = {}
                _temp_key = _key

                _schema = _request_obj.get("schema")
                _value = _request_obj.get(_temp_key)
                _name = _request_obj.get("name")
                _type = _request_obj.get("type")
                _enum = _request_obj.get("enum")

                if _temp_key in ["responses"]:
                    continue

                if _temp_key == "requestBody":
                    _value = "body"
                    _temp_key = "in"

                    if _request_obj.get("requestBody").get("content").get("application/json") is not None:
                        _schema = _request_obj.get("requestBody").get("content").get("application/json").get("schema")
                    elif _request_obj.get("requestBody").get("content").get("multipart/form-data") is not None:
                        _schema = _request_obj.get("requestBody").get("content").get("multipart/form-data").get("schema")

                if _schema is None:
                    _schema = _request_obj

                if _temp_key == "in":

                    _new_value = self.randomValueGenerator(_name, _type, _schema)

                    if _value == "path":

                        if _output_obj.get("path") is not None:
                            _path = _output_obj.get("path")

                        _temp_value = None

                        if type(_new_value) == dict:
                            _temp_value = str(_new_value.get(_name))
                        elif type(_new_value) == list:
                            _temp_value = ",".join(str(v) for v in _new_value)
                        else:
                            _temp_value = str(_new_value)

                        _path = str(_path).replace("{" + _name + "}", _temp_value)

                        _output_obj["path"] = _path

                    elif _value == "query":

                        if _output_obj.get("query_string") is None:
                            _output_obj["query_string"] = {}

                        if type(_new_value) == dict:
                            _temp_value = _new_value.get(_name)

                            for _query_key in _new_value.keys():
                                _output_obj["query_string"][_query_key] = _new_value.get(_query_key)

                        else:
                            _output_obj["query_string"][_name] = _new_value


                    elif _value == "header":

                        if _output_obj.get("header") is None:
                            _output_obj["header"] = {}

                        _output_obj["header"][_name] = str(_new_value.get(_name))

                    elif _value == "body":

                        _output_obj["body"] = _new_value

                        if _output_obj.get("header") is None:
                            _output_obj["header"] = {}

                        _output_obj["header"]["Content-Type"] = "application/json"

                    elif _value == "formData":

                        #application/x-www-form-urlencoded or multipart/form-data

                        _output_obj["formData"] = _new_value

                        if _output_obj.get("header") is None:
                            _output_obj["header"] = {}

                        _output_obj["header"]["Content-Type"] = "application/x-www-form-urlencoded"

                        #todo

                if type(_request_obj.get(_key)) == str:
                    continue
                self.generateRequest(_path, _method, _request_obj.get(_key), _output_obj)
        elif type(_request_obj) == list:
            for _item in _request_obj:
                if type(_item) == str:
                    continue
                self.generateRequest(_path, _method, _item, _output_obj)
        else:
            "" #for debugging

        if _output_obj.get("path") is None:
            _output_obj["path"] = _path

        _output_obj["method"] = _method

        return _output_obj


    def parseResponse(self, _url, _response):
        global SERVICE_URL

        _swagger_raw_json = ""
        _swagger_json_object = {}

        if "/swagger/swagger-ui-init.js" in _url or "/docs/swagger-ui-init.js" in _url:
            _search_result = re.search("[var|let] options = (.*?);", str(_response).replace("\n",""))

            if _search_result and len(_search_result.groups()) > 0:
                _swagger_raw_json = _search_result.groups()[0]
                _swagger_raw_json = _swagger_raw_json.replace("\n", "").replace("  ", "").replace("\\n", "")
                _temp_json_obj = json.loads(_swagger_raw_json)
                if "swaggerDoc" in _temp_json_obj.keys():
                    _swagger_json_object = _temp_json_obj["swaggerDoc"]
        else:
            _swagger_json_object = json.loads(_response)

        _parsed_swagger_json_object = self.findAndParseAllRefs(_swagger_json_object, _swagger_json_object)

        _total_path = 0
        _endpoints = []
        _markup_endpoints = []

        _root_url = self.getRootUrl(self.swagger_url)

        for _path in _swagger_json_object["paths"].keys():
            _path_obj = _swagger_json_object["paths"][_path]

            if len(_path_obj.keys()) > 0:
                for _method in _path_obj.keys():
                    _method_obj = _path_obj[_method]

                    _temp_tag = "default"

                    if "tags" in _method_obj.keys():
                        _temp_tag = _method_obj["tags"][0]



                    _all_root_keys = list(_method_obj.keys())

                    for _key in _all_root_keys:
                        if _key not in ["parameters", "requestBody"]:
                            _method_obj.pop(_key)

                    _request_obj = self.generateRequest(_path, _method, _method_obj, {})

                    _request_obj["raw_path"] = _path

                    _markup_endpoints.append("- [ ] " + str(_method).upper() + " " + _path)
                    _endpoints.append(_request_obj)


            _total_path += len(_swagger_json_object["paths"][_path].keys())

        print("Total endpoint: " + str(_total_path))

        basePath = ""

        if _swagger_json_object.get("basePath") != None:
            basePath = _swagger_json_object.get("basePath")

        return {"endpoints": _endpoints, "base_path": basePath, "markup_endpoints": _markup_endpoints}


    def generateQueryString(self, param_obj):
        param_obj = dict(param_obj)
        temp_query_string = ""

        for _key in param_obj.keys():

            _value = param_obj.get(_key)

            if type(_value) == list:
                _value = json.dumps(_value)
            else:
                _value = str(_value)

            temp_query_string += str(_key) + "=" + _value + "&"


        if temp_query_string.endswith("&"):
            temp_query_string = temp_query_string.strip("&")

        return temp_query_string

    def bytesToString(self, _bytes):

        char_arr = []

        for b in _bytes:
            print(b)
            if b < 257 and b > -1:
                char_arr.append(chr(b))

        return "".join(char_arr)

    def getRootUrl(self, _url):

        _protocol = "https://"

        if str(_url).startswith("https://"):
            _protocol = "https://"
        elif str(_url).startswith("http://"):
            _protocol = "http://"


        _url = str(_url).replace(_protocol, "")

        if "/" in _url:
            _url = str(_url).split("/")[0]

        return _protocol + _url


class MenuClickListener(MouseAdapter):
    def __init__(self, extender, invocation):
        self._extender = extender
        self._invocation = invocation

    def mouseReleased(self, e):
        self._extender.menuItemClicked(self._invocation)


class TableMenuClickListener(MouseAdapter):
    def __init__(self, extender, invocation):
        self._extender = extender
        self._invocation = invocation

    def mouseReleased(self, e):
        #self._extender.menuItemClicked(self._invocation)
        global popup_menu

        if e.getButton() == MouseEvent.BUTTON3:
            popup_menu.show(e.getComponent(), e.getX(), e.getY())

header_text_editor = None
output_text_editor = None
history_table = None
popup_menu = None
extracted_requests = []
output_scroll_pane = None
parsable_docs_combobox = None
parsable_docs = {}

class SwaggerParserTab(ITab):
    parent_self = None

    def __init__(self, callbacks, parent):
        self._callbacks = callbacks
        self.parent_self = parent

    class NonEditableTableModel(DefaultTableModel):
        def isCellEditable(self, row, column):
            return False

    def getTabCaption(self):
        return "Swagger Parser"

    def getSelectedComboboxItem(self, event):
        global parsable_docs_combobox
        global parsable_docs

        selected_item = parsable_docs_combobox.getSelectedItem()

        if selected_item != None:
            self.parent_self.startParseFromUI(parsable_docs[str(selected_item)])

    def getUiComponent(self):
        global header_text_editor
        global output_text_editor
        global history_table
        global output_scroll_pane
        global parsable_docs_combobox

        main_panel = JPanel()
        layout = GroupLayout(main_panel)
        main_panel.setLayout(layout)
        layout.setAutoCreateGaps(True)
        layout.setAutoCreateContainerGaps(True)

        header_label = JLabel("Custom Headers")
        header_text_editor = JTextPane()
        header_text_editor.setText("X-Forwarded-For: 127.0.0.1\nAuthorization: Bearer [TOKEN]")
        header_scroll_pane = JScrollPane(header_text_editor)

        output_label = JLabel("")
        output_text_editor = JTextPane()
        output_scroll_pane = JScrollPane(output_text_editor)

        table_model = self.NonEditableTableModel()
        table_model.addColumn("Request Method")
        table_model.addColumn("URL")
        table_model.addColumn("Status Code")
        table_model.addColumn("Response Length")

        parsable_docs_combobox = JComboBox([])
        add_button = JButton("Start", actionPerformed=self.getSelectedComboboxItem)

        history_table = JTable(table_model)
        history_scroll_pane = JScrollPane(history_table)

        history_table.addMouseListener(TableMenuClickListener(self, history_table))

        screen_size = Toolkit.getDefaultToolkit().getScreenSize()
        screen_height = screen_size.getHeight()
        screen_width = screen_size.getWidth()

        output_components_max_height = int(screen_height / 3)
        output_components_max_width = int(screen_width / 2)

        header_scroll_pane.setMaximumSize(
            Dimension(output_components_max_width, output_components_max_height))
        output_scroll_pane.setMaximumSize(Dimension(output_components_max_width, output_components_max_height))

        output_text_editor.setPreferredSize(Dimension(output_components_max_width, output_components_max_height))


        layout.setHorizontalGroup(
            layout.createParallelGroup()
            .addGroup(layout.createSequentialGroup()
                      .addComponent(header_label)
                      .addComponent(parsable_docs_combobox)
                      .addComponent(add_button)
                      .addComponent(output_label))
            .addGroup(layout.createSequentialGroup()
                      .addComponent(header_scroll_pane)
                      .addComponent(output_scroll_pane))
            .addComponent(history_scroll_pane)
        )

        layout.setVerticalGroup(
            layout.createSequentialGroup()
            .addGroup(layout.createParallelGroup(GroupLayout.Alignment.BASELINE)
                      .addComponent(header_label)
                      .addComponent(parsable_docs_combobox)
                      .addComponent(add_button)
                      .addComponent(output_label))
            .addGroup(layout.createParallelGroup(GroupLayout.Alignment.BASELINE)
                      .addComponent(header_scroll_pane)
                      .addComponent(output_scroll_pane))
            .addComponent(history_scroll_pane)
        )

        return main_panel

class SequentialThread(threading.Thread):
    def __init__(self, func, args):
        super(SequentialThread, self).__init__()
        self.func = func
        self.args = args

    def run(self):
        self.func(*self.args)

class BurpExtender(IBurpExtender, IContextMenuFactory, IProxyListener):

    def bytesToString(self, _bytes):

        char_arr = []

        for b in _bytes:
            if b < 257 and b > -1:
                char_arr.append(chr(b))

        return "".join(char_arr)

    def registerExtenderCallbacks(self, callbacks):
        global popup_menu

        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        callbacks.setExtensionName("Swagger Parser")


        popup_menu = JPopupMenu()
        menu_item = JMenuItem("Send to Repeater")
        menu_item.addActionListener(self.tableMenuItemClickedToRepeater)
        popup_menu.add(menu_item)
        menu_item = JMenuItem("Send to Intruder")
        menu_item.addActionListener(self.tableMenuItemClickedToIntruder)
        popup_menu.add(menu_item)
        menu_item = JMenuItem("Send to Scanner")
        menu_item.addActionListener(self.tableMenuItemClickedToScanner)
        popup_menu.add(menu_item)


        callbacks.registerContextMenuFactory(self)

        callbacks.registerProxyListener(self)

        tab = SwaggerParserTab(callbacks, self)
        callbacks.addSuiteTab(tab)

    def createMenuItems(self, invocation):
        self.invocation = invocation
        menuList = ArrayList()

        menuItem = JMenuItem("Send to Swagger Parser")
        menuItem.addMouseListener(MenuClickListener(self, invocation))


        menuList.add(menuItem)

        history_table.addMouseListener(TableMenuClickListener(self, invocation))


        return menuList

    def processProxyMessage(self, messageIsRequest, message):
        global parsable_docs
        global parsable_docs_combobox

        if not messageIsRequest:
            message = message.getMessageInfo()

            request = message.getRequest()

            analyzedRequest = self._helpers.analyzeRequest(request)

            doc_url = str(message.getUrl().toString()).strip()

            response = message.getResponse()
            analyzedResponse = self._helpers.analyzeResponse(response)
            headers = analyzedResponse.getHeaders()
            responseBody = response[analyzedResponse.getBodyOffset():].tostring()

            if ("swagger" in responseBody or "openapi" in responseBody) and "paths" in responseBody and "info" in responseBody and (doc_url.endswith(".json") or "api-docs" in doc_url or doc_url.endswith("swagger-ui-init.js")):
                parsable_docs[doc_url] = message

                parsable_docs_combobox_item_count = parsable_docs_combobox.getItemCount()

                if parsable_docs_combobox_item_count == 0:
                    parsable_docs_combobox.addItem(doc_url)
                else:
                    for i in range(parsable_docs_combobox_item_count):
                        item = str(parsable_docs_combobox.getItemAt(i)).strip()
                        if item != doc_url:
                            parsable_docs_combobox.addItem(doc_url)



    def tableMenuItemClickedToScanner(self, event):
        global history_table
        global extracted_requests

        selected_rows = history_table.getSelectedRows()

        for selected_row in selected_rows:

            request_item = extracted_requests[selected_row]
            http_service = request_item["http_service"]
            http_request = request_item["http_request"]

            is_https = True

            if http_service.getProtocol() != "https":
                is_https = False

            self._callbacks.doActiveScan(http_service.getHost(), http_service.getPort(), is_https,
                                           http_request)

    def tableMenuItemClickedToIntruder(self, event):
        global history_table
        global extracted_requests

        selected_rows = history_table.getSelectedRows()

        for selected_row in selected_rows:

            request_item = extracted_requests[selected_row]
            http_service = request_item["http_service"]
            http_request = request_item["http_request"]

            is_https = True

            if http_service.getProtocol() != "https":
                is_https = False


            self._callbacks.sendToIntruder(http_service.getHost(), http_service.getPort(), is_https,
                                           http_request, None)


    def tableMenuItemClickedToRepeater(self, event):
        global history_table
        global extracted_requests

        selected_rows = history_table.getSelectedRows()

        for selected_row in selected_rows:

            request_item = extracted_requests[selected_row]
            http_service = request_item["http_service"]
            http_request = request_item["http_request"]

            is_https = True

            if http_service.getProtocol() != "https":
                is_https = False


            title_endpoint = str(request_item["request_url"]).split("?")[0].split("#")[0]

            tab_title = request_item["request_method"] + " " + title_endpoint

            self._callbacks.sendToRepeater(http_service.getHost(), http_service.getPort(), is_https,
                                           http_request, tab_title)


    def runParser(self, traffic, main_url):
        global header_text_editor
        global output_text_editor
        global output_scroll_pane

        request_info = self._helpers.analyzeRequest(traffic)
        request_headers = request_info.getHeaders()
        request_body = traffic.getRequest()[request_info.getBodyOffset():]

        response = traffic.getResponse()
        response_info = self._helpers.analyzeResponse(response)

        response_headers = response_info.getHeaders()
        response_body_bytes = response[response_info.getBodyOffset():]

        http_version = str(request_headers[0]).split(" ")[-1]
        basic_headers = request_headers[1:]

        response_body_str = self.bytesToString(response_body_bytes)

        swagger_parser = SwaggerParser(swagger_url=main_url, headers={})

        parsed_swagger = swagger_parser.parseResponse(main_url, response_body_str)

        endpoints = parsed_swagger.get("endpoints")

        self.resetTable()

        for endpoint in endpoints:

            temp_query_string_dict = endpoint.get("query_string")

            temp_path = parsed_swagger.get("base_path")
            temp_path += endpoint.get("path")

            temp_headers_dict = {}


            if temp_query_string_dict != None:
                temp_path += "?" + swagger_parser.generateQueryString(temp_query_string_dict)

            temp_first_header = endpoint.get("method").upper() + " " + temp_path + " " + http_version
            temp_headers = [temp_first_header]


            #temp_headers.extend(basic_headers)

            for basic_header in basic_headers:
                if ":" in basic_header:
                    basic_header_key_value = basic_header.split(":")
                    temp_headers_dict[basic_header_key_value[0]] = ":".join(basic_header_key_value[1:])

            temp_custom_headers_dict = endpoint.get("header")  # from swagger

            if temp_custom_headers_dict != None:

                temp_custom_headers_dict = dict(endpoint.get("header"))

                for _key in temp_custom_headers_dict.keys():
                    temp_headers_dict[_key] = temp_custom_headers_dict.get(_key)

            custom_headers_from_ui = str(header_text_editor.getText()).split("\n")  # from ui

            for custom_header_from_ui in custom_headers_from_ui:
                clean_custom_header_from_ui = custom_header_from_ui.strip()  # todo
                if clean_custom_header_from_ui != "" and ":" in clean_custom_header_from_ui:
                    clean_custom_header_from_ui_key_value = clean_custom_header_from_ui.split(":")
                    temp_headers_dict[clean_custom_header_from_ui_key_value[0]] = ":".join(clean_custom_header_from_ui_key_value[1:])

            for header_key in temp_headers_dict.keys():
                temp_headers.append(header_key + ":" + temp_headers_dict.get(header_key))

            temp_body = endpoint.get("body")

            if temp_body != None:
                temp_body = json.dumps(temp_body)
            else:
                temp_body = endpoint.get("formData")

                if temp_body != None:
                    temp_body = swagger_parser.generateQueryString(temp_body)
                else:
                    temp_body = ""

            get_swagger_request = self._helpers.buildHttpMessage(temp_headers, temp_body)

            threads = []

            temp_thread = SequentialThread(self.makeHttpRequest, (traffic.getHttpService(), get_swagger_request,
                                   "/".join(main_url.split("/")[:3]) + temp_path,
                                   endpoint.get("method").upper()))

            threads.append(temp_thread)

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join()

        markup_endpoints = parsed_swagger.get("markup_endpoints")

        output_markup_endpoints = main_url + "\n\n"

        for markup_endpoint in markup_endpoints:
            output_markup_endpoints += markup_endpoint + "\n"

        output_markup_endpoints += "\nTotal: " + str(len(markup_endpoints))

        output_markup_endpoints += "\n\n"

        output_text_editor.setText(output_markup_endpoints)

        output_scroll_pane.revalidate()
        output_scroll_pane.repaint()

    def resetTable(self):
        global history_table
        global extracted_requests



        table_model = history_table.getModel()
        while table_model.getRowCount() > 0:
            table_model.removeRow(0)

        extracted_requests = []

    def loadingOutputEditor(self):
        global output_text_editor

        output_text_editor.setText("Loading...")

    def loadingTable(self):
        global history_table

        table_model = history_table.getModel()
        table_model.addRow(["Loading...", "Loading...", "Loading...", "Loading..."])

    def startParseFromUI(self, traffic):
        if traffic.getUrl() != None:
            main_url = str(traffic.getUrl().toString())

            if main_url.endswith(".json") or "api-docs" in main_url or main_url.endswith("swagger-ui-init.js"):
                self.resetTable()
                self.loadingTable()
                self.loadingOutputEditor()

                threading.Thread(target=self.runParser,
                                 args=(traffic, main_url)).start()

    def menuItemClicked(self, event):
        global header_text_editor
        global output_text_editor
        global output_scroll_pane
        global history_table


        httpTraffic = self.invocation.getSelectedMessages()

        for traffic in httpTraffic:

            self.startParseFromUI(traffic)


    def makeHttpRequest(self, target_service, post_request, request_url, request_method):
        global history_table
        global extracted_requests

        if str(request_url).strip() == "" or str(request_method).strip() == "":
            return

        try:
            response = self._callbacks.makeHttpRequest(target_service, post_request)

            if response:
                response_info = self._helpers.analyzeResponse(response.getResponse())
                response_headers = response_info.getHeaders()
                response_body = response.getResponse()[response_info.getBodyOffset():]



                response_body_str = self.bytesToString(response_body)


                table_model = history_table.getModel()
                row_data = [request_method, request_url, response_info.getStatusCode(), len(response_body_str)]
                table_model.addRow(row_data)

                extracted_requests.append(
                    {"http_service": target_service, "http_request": post_request, "request_method": request_method, "request_url": request_url})


        except Exception as e:
            print("table_model add row err")
            print(e)

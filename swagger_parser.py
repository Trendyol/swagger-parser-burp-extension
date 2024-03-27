from burp import IBurpExtender
from burp import IProxyListener
from burp import IContextMenuFactory
from java.util import ArrayList
from javax.swing import JMenuItem
from java.awt.event import MouseAdapter, MouseEvent
from javax.swing import (JTabbedPane, DefaultComboBoxModel, BoxLayout,GroupLayout, JPanel, JComboBox, JCheckBox, JTextField, JTextArea, JLabel, JButton, JScrollPane, JTable, JPopupMenu, JTextPane, JFrame)
from java.awt import (Insets, BorderLayout, GridBagLayout, GridBagConstraints, Dimension, Toolkit, FlowLayout, GridLayout)
from javax import swing
from burp import ITab
from javax.swing.table import (DefaultTableModel)
import javax.swing.KeyStroke as KeyStroke
import java.awt.event.KeyEvent as KeyEvent
import javax.swing.AbstractAction as AbstractAction
import java.awt.event.ComponentAdapter as ComponentAdapter

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


main_panel = None
header_text_editor = None
request_detail_text_editor = None
output_text_editor = None
history_table = None
popup_menu = None
extracted_requests = []
output_scroll_pane = None
parsable_docs_combobox = None
parsable_docs = {}
popup_frame = None
remove_confirmation_popup_frame = None
global_parent_self = None
tabbedPane = None
tabbedPane2 = None


def isValidSwaggerDoc(doc):
    doc = str(doc)
    return (doc.startswith("http://") or doc.startswith("https://")) and (
                doc.endswith("json") or "api-docs" in doc or doc.endswith("swagger-ui-init.js"))

class MenuClickListener(MouseAdapter):
    def __init__(self, extender, invocation):
        self._extender = extender
        self._invocation = invocation

    def mouseReleased(self, e):
        self._extender.menuItemClicked(self._invocation)

last_table_selections = []


class MoveAction(AbstractAction):
    def __init__(self, table, direction):
        self.table = table
        self.direction = direction

    def actionPerformed(self, e):
        row = self.table.getSelectedRow() + self.direction

        if row >= 0 and row < self.table.getRowCount():
            self.table.setRowSelectionInterval(row, row)

            request_item = extracted_requests[row]

            http_request = request_item["http_request"]

            request_detail_text_editor.setText(global_parent_self._helpers.bytesToString(http_request))

            tabbedPane.setSelectedIndex(1)


class TableMenuClickListener(MouseAdapter):
    def __init__(self, extender, invocation):
        self._extender = extender
        self._invocation = invocation

    def mouseReleased(self, e):
        global popup_menu
        global history_table
        global header_text_editor
        global last_table_selections
        global extracted_requests
        global global_parent_self
        global request_detail_text_editor
        global tabbedPane

        if e.getButton() == MouseEvent.BUTTON3:
            popup_menu.show(e.getComponent(), e.getX(), e.getY())

        if e.getButton() == MouseEvent.BUTTON1:
            current_selections = list(history_table.getSelectedRows())

            temp_selection = list(set(current_selections) - set(last_table_selections))
            single_selection = -1

            if len(temp_selection) > 0:
                single_selection = temp_selection[0]

            if single_selection != -1:

                request_item = extracted_requests[single_selection]

                http_request = request_item["http_request"]

                request_detail_text_editor.setText(global_parent_self._helpers.bytesToString(http_request))

                tabbedPane.setSelectedIndex(1)

            last_table_selections = current_selections



class RemoveConfirmationPopup(swing.JPanel):
    parent_self = None

    def __init__(self, remove_all, parent):
        super(RemoveConfirmationPopup, self).__init__()

        self.parent_self = parent
        popup_title = "Are you sure you want to remove Selected Items?"

        if remove_all:
            popup_title = "Are you sure you want to remove All Items?"

        layout = GridBagLayout()
        self.setLayout(layout)
        gbc = GridBagConstraints()

        label = swing.JLabel(popup_title)
        gbc.gridx = 0
        gbc.gridy = 0
        gbc.gridwidth = 2
        gbc.insets = Insets(5, 5, 5, 5)
        self.add(label, gbc)

        blank_panel = swing.JPanel()
        blank_panel.setPreferredSize(Dimension(1, 100))
        gbc.gridx = 0
        gbc.gridy = 1
        gbc.gridwidth = 2
        self.add(blank_panel, gbc)

        button_panel = swing.JPanel()
        button_panel.setLayout(GridLayout(1, 2, 10, 0))

        no_button = swing.JButton("No", actionPerformed=self.close_popup)
        no_button.setPreferredSize(Dimension(60, 25))
        button_panel.add(no_button)

        if remove_all:
            yes_button = swing.JButton("Yes", actionPerformed=self.confirm_all_removal)
            yes_button.setPreferredSize(Dimension(60, 25))
            button_panel.add(yes_button)
        else:
            yes_button = swing.JButton("Yes", actionPerformed=self.confirm_removal)
            yes_button.setPreferredSize(Dimension(60, 25))
            button_panel.add(yes_button)



        gbc.gridx = 0
        gbc.gridy = 2
        gbc.gridwidth = 2
        gbc.insets = Insets(0, 0, 10, 0)
        self.add(button_panel, gbc)

    def close_popup(self, event):
        frame = swing.SwingUtilities.getWindowAncestor(self)
        frame.dispose()

    def confirm_all_removal(self, event):
        self.parent_self.clearTable(event)
        self.close_popup(None)

    def confirm_removal(self, event):
        self.parent_self.removeSelectedItems(event)
        self.close_popup(None)


class ResizeListener(ComponentAdapter):
    def componentResized(self, e):

        if main_panel is not None:
            screen_size = main_panel.getSize()
            screen_height = screen_size.height
            screen_width = screen_size.width

            output_components_max_height = int(screen_height / 3)
            output_components_max_width = int(screen_width / 2)

            tabbedPane.setMinimumSize(
                Dimension(output_components_max_width - 10, output_components_max_height))

            tabbedPane.setMaximumSize(
                Dimension(output_components_max_width - 10, output_components_max_height))

            tabbedPane2.setMinimumSize(
                Dimension(output_components_max_width - 10, output_components_max_height - 2))

            tabbedPane2.setMaximumSize(
                Dimension(output_components_max_width - 10, output_components_max_height - 2))


class SwaggerParserTab(ITab):
    parent_self = None

    def __init__(self, callbacks, parent):
        global global_parent_self

        self._callbacks = callbacks
        self.parent_self = parent
        global_parent_self = parent

    class NonEditableTableModel(DefaultTableModel):
        def isCellEditable(self, row, column):
            return False

    def getTabCaption(self):
        return "Swagger Parser"

    def stringToBytes(self, text, encoding='utf-8'):
        return text.encode(encoding)

    def bytesToString(self, _bytes):

        char_arr = []

        for b in _bytes:
            if b < 257 and b > -1:
                char_arr.append(chr(b))

        return "".join(char_arr)

    def sendHttpRequest(self, url):
        global parsable_docs

        url = str(url)

        protocol = "https"
        port = 443

        if not url.startswith(protocol):
            protocol = "http"
            port = 80

        hostname = url.replace(protocol + "://", "").split("/")[0]

        if ":" in hostname:
            temp_hostname_split = hostname.split(":")
            hostname = temp_hostname_split[0]
            port = int(temp_hostname_split[1])


        if port in [80, 443]:
            temp_url_1 = url.replace("://" + hostname + "/", "://" + hostname + ":" + str(port) + "/")
            temp_url_2 = url.replace("://" + hostname + ":" + str(port) + "/", "://" + hostname + "/")

            if temp_url_1 != temp_url_2 and temp_url_1 in list(parsable_docs.keys()) and temp_url_2 in list(parsable_docs.keys()):
                    del parsable_docs[temp_url_1]
                    url = temp_url_2



        swagger_doc_path = url.replace(protocol + "://" + hostname, "")

        http_service = self.parent_self._helpers.buildHttpService(hostname, port, protocol)

        request = "GET " + swagger_doc_path + " HTTP/2\r\nHost: " + hostname + "\r\n\r\n"


        def make_request():
            global parsable_docs

            response = self.parent_self._callbacks.makeHttpRequest(http_service, request.encode())

            ref_url = str(response.getUrl())

            parsable_docs[ref_url] = response


        thread = threading.Thread(target=make_request)
        thread.start()

        return

    def add_component(self, component, gridx, gridy, anchor):
        gbc = GridBagConstraints()
        gbc.gridx = gridx
        gbc.gridy = gridy
        gbc.anchor = anchor
        self.right_panel.add(component, gbc)


    def openRemoveConfirmationPopup(self, event, remove_all):
        global remove_confirmation_popup_frame

        if remove_confirmation_popup_frame is not None:
            remove_confirmation_popup_frame.dispose()

        frame_width = 300

        if not remove_all:
            frame_width = 320

        remove_confirmation_popup_frame = JFrame("Confirm", size=(frame_width, 125))
        remove_confirmation_popup_frame.setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE)
        remove_confirmation_popup_frame.setLayout(BorderLayout())
        remove_confirmation_popup_frame.setResizable(False)

        remove_confirmation_popup = RemoveConfirmationPopup(remove_all, self)
        remove_confirmation_popup_frame.add(remove_confirmation_popup)

        remove_confirmation_popup_frame.setLocationRelativeTo(None)
        remove_confirmation_popup_frame.setVisible(True)

    def addNewUrl(self, event):
        global popup_frame

        if popup_frame is not None:
            popup_frame.dispose()

        popup_frame = JFrame("Add New Swagger Document", size=(612, 300))
        popup_frame.setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE)
        popup_frame.setLayout(BorderLayout())
        popup_frame.setResizable(False)

        self.main_panel = JPanel()
        self.main_panel.setLayout(BorderLayout())
        self.main_panel.setPreferredSize(Dimension(608, 300))

        self.left_panel = JPanel()
        self.left_panel.setLayout(BorderLayout())

        self.text_field = JTextField(20)
        self.text_field.setPreferredSize(Dimension(500, 25))

        self.table_model = self.NonEditableTableModel()
        self.table_model.addColumn("URL")

        temp_combobox_items = self.getComboboxItems()

        if len(temp_combobox_items) > 0:
            for item in temp_combobox_items:
                self.table_model.addRow([item])

        self.table = JTable(self.table_model)
        self.table.setPreferredScrollableViewportSize(Dimension(500, 150))
        self.table.setTableHeader(None)

        self.scroll_pane = JScrollPane(self.table)

        self.left_panel.add(self.text_field, BorderLayout.NORTH)
        self.left_panel.add(self.scroll_pane, BorderLayout.CENTER)

        self.right_panel = JPanel()
        self.right_panel.setPreferredSize(Dimension(110, 300))
        self.right_panel.setLayout(GridBagLayout())

        self.button1 = JButton("Add")
        self.button2 = JButton("Remove")
        self.button3 = JButton("Remove All")

        self.empty_panel = JPanel()
        self.empty_panel.setPreferredSize(Dimension(10, 176))

        button_size = Dimension(100, 25)
        self.button1.setPreferredSize(button_size)
        self.button2.setPreferredSize(button_size)
        self.button3.setPreferredSize(button_size)

        gbc = GridBagConstraints()
        gbc.fill = GridBagConstraints.HORIZONTAL
        gbc.anchor = GridBagConstraints.NORTHWEST

        gbc.insets = Insets(2, 0, 2, 0)
        gbc.gridx = 0
        gbc.gridy = 0
        self.right_panel.add(self.button1, gbc)

        gbc.gridy = 1
        self.right_panel.add(self.button2, gbc)

        gbc.gridy = 2
        self.right_panel.add(self.button3, gbc)

        gbc.gridy = 3
        self.right_panel.add(self.empty_panel, gbc)

        self.button1.addActionListener(self.addUrlToTable)
        self.button2.addActionListener(lambda event: self.openRemoveConfirmationPopup(event, False))
        self.button3.addActionListener(lambda event: self.openRemoveConfirmationPopup(event, True))

        self.main_panel.add(self.left_panel, BorderLayout.WEST)
        self.main_panel.add(self.right_panel, BorderLayout.EAST)

        popup_frame.add(self.main_panel, BorderLayout.CENTER)

        popup_frame.setLocationRelativeTo(None)
        popup_frame.setVisible(True)


    def syncTables(self):
        global parsable_docs
        global parsable_docs_combobox

        model = self.table.getModel()
        model.setRowCount(0)

        parsable_docs_combobox.setModel(DefaultComboBoxModel([]))

        for doc_item in sorted(list(dict(parsable_docs).keys())):
            model.addRow([doc_item])
            parsable_docs_combobox.addItem(doc_item)

    def addToParcableDocsDict(self, new_item):
        global parsable_docs

        if new_item not in list(dict(parsable_docs).keys()):
            parsable_docs[new_item] = "" #TODO request will be generate

            self.sendHttpRequest(new_item)

    def addUrlToTable(self, event):
        global parsable_docs

        text = str(self.text_field.getText())

        if not isValidSwaggerDoc(text):
            return

        self.addToParcableDocsDict(text)
        self.syncTables()

        self.text_field.setText("")
        self.text_field.requestFocus()

    def removeSelectedItems(self, event):
        global parsable_docs

        selected_rows = list(self.table.getSelectedRows())
        table_model = self.table.getModel()
        table_changed = False

        for row in selected_rows:
            value = table_model.getValueAt(row, 0)
            if value in parsable_docs.keys():
                del parsable_docs[value]
                table_changed = True


        if table_changed:
            self.syncTables()



    def clearTable(self, event):
        global parsable_docs
        parsable_docs = {}
        self.syncTables()
        self.text_field.requestFocus()


    def getComboboxItems(self):
        global parsable_docs
        return sorted(list(dict(parsable_docs).keys()))

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
        global request_detail_text_editor
        global tabbedPane
        global tabbedPane2
        global main_panel

        main_panel = JPanel()
        main_panel.addComponentListener(ResizeListener())
        layout = GroupLayout(main_panel)
        main_panel.setLayout(layout)
        layout.setAutoCreateGaps(True)
        layout.setAutoCreateContainerGaps(True)

        header_label = JLabel("Swagger Docs: ")
        header_text_editor = JTextPane()
        header_text_editor.setText("X-Forwarded-For: 127.0.0.1\nAuthorization: Bearer [TOKEN]")
        header_scroll_pane = JScrollPane(header_text_editor)

        request_detail_text_editor = JTextPane()
        request_detail_text_editor.setText("")
        request_detail_scroll_pane = JScrollPane(request_detail_text_editor)



        tabbedPane = JTabbedPane()

        tabbedPane.addTab("Custom Headers", header_scroll_pane)
        tabbedPane.addTab("Request Detail", request_detail_scroll_pane)



        output_label = JLabel("")
        output_text_editor = JTextPane()
        output_scroll_pane = JScrollPane(output_text_editor)

        tabbedPane2 = JTabbedPane()

        tabbedPane2.addTab("Output", output_scroll_pane)

        table_model = self.NonEditableTableModel()
        table_model.addColumn("Method")
        table_model.addColumn("URL")
        table_model.addColumn("Status Code")
        table_model.addColumn("Length")

        parsable_docs_combobox = JComboBox([])
        add_button = JButton("Start Parsing", actionPerformed=self.getSelectedComboboxItem)
        add_button2 = JButton("Add New Doc", actionPerformed=self.addNewUrl)

        history_table = JTable(table_model)

        column_model = history_table.getColumnModel()
        column_model.getColumn(0).setMinWidth(80)
        column_model.getColumn(0).setMaxWidth(80)
        column_model.getColumn(2).setMinWidth(120)
        column_model.getColumn(2).setMaxWidth(120)
        column_model.getColumn(3).setMinWidth(80)
        column_model.getColumn(3).setMaxWidth(80)

        history_scroll_pane = JScrollPane(history_table)

        history_table.addMouseListener(TableMenuClickListener(self, history_table))

        input_map = history_table.getInputMap()
        action_map = history_table.getActionMap()

        input_map.put(KeyStroke.getKeyStroke(KeyEvent.VK_UP, 0), "Up")
        action_map.put("Up", MoveAction(history_table, -1))

        input_map.put(KeyStroke.getKeyStroke(KeyEvent.VK_DOWN, 0), "Down")
        action_map.put("Down", MoveAction(history_table, 1))

        screen_size = Toolkit.getDefaultToolkit().getScreenSize()
        screen_height = screen_size.getHeight()
        screen_width = screen_size.getWidth()

        output_components_max_height = int(screen_height / 3)
        output_components_max_width = int(screen_width / 2)

        tabbedPane.setMinimumSize(
            Dimension(output_components_max_width - 10, output_components_max_height))

        tabbedPane.setMaximumSize(
            Dimension(output_components_max_width - 10, output_components_max_height))

        tabbedPane2.setMinimumSize(
            Dimension(output_components_max_width - 10, output_components_max_height - 2))

        tabbedPane2.setMaximumSize(
            Dimension(output_components_max_width - 10, output_components_max_height - 2))


        layout.setHorizontalGroup(
            layout.createParallelGroup()
            .addGroup(layout.createSequentialGroup()
                      .addComponent(header_label)
                      .addComponent(parsable_docs_combobox)
                      .addComponent(add_button)
                      .addComponent(add_button2)
                      .addComponent(output_label))
            .addGroup(layout.createSequentialGroup()
                      .addComponent(tabbedPane)
                      .addComponent(tabbedPane2))
            .addComponent(history_scroll_pane)
        )

        layout.setVerticalGroup(
            layout.createSequentialGroup()
            .addGroup(layout.createParallelGroup(GroupLayout.Alignment.BASELINE)
                      .addComponent(header_label)
                      .addComponent(parsable_docs_combobox)
                      .addComponent(add_button)
                      .addComponent(add_button2)
                      .addComponent(output_label))
            .addGroup(layout.createParallelGroup(GroupLayout.Alignment.BASELINE)
                      .addComponent(tabbedPane)
                      .addComponent(tabbedPane2))
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

            if ("swagger" in responseBody or "openapi" in responseBody) and "paths" in responseBody and "info" in responseBody and (doc_url.endswith("json") or "api-docs" in doc_url or doc_url.endswith("swagger-ui-init.js")):
                parsable_docs[doc_url] = message

                parsable_docs_combobox.setModel(DefaultComboBoxModel([]))
                for doc_item in sorted(list(dict(parsable_docs).keys())):
                    parsable_docs_combobox.addItem(doc_item)




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

            if isValidSwaggerDoc(main_url):
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

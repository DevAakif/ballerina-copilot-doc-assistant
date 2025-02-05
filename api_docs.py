import json
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import AzureChatOpenAI
from utils.libs.libraryLinks import library_links

llm = AzureChatOpenAI(
    azure_deployment="gpt4o-mini",
    api_version="2023-07-01-preview",
    temperature=0
)

context_json = "utils/libs/context.json"
libs_json = "utils/libs/libs.json"


def pull_central(context_path: str, libs_path: str):
    with open(context_path, 'r', encoding='utf-8') as file:
        context_data = json.load(file)

    with open(libs_path, 'r', encoding='utf-8') as file:
        libs_data = json.load(file)

    for lib in libs_data:
        context_data.append(lib)

    return context_data


def get_libraries(usecase: str, context_path: str, libs_path: str):

    minified_context = []
    central_docs_context = pull_central(context_path, libs_path)
    for lib in central_docs_context:
        minified_lib = {
            "name": lib["name"],
            "description": lib["description"]
        }
        minified_context.append(minified_lib)

    messages = [
        (
            "system",
            "You are an assistant tasked with selecting all the Ballerina libraries needed to answer a specific question from a given set of libraries provided in the context as a JSON. RESPOND ONLY WITH A JSON.",
        ),
        ("human",
         f"""
            # Library Context JSON
            ${str(minified_context)}
            # QUESTION
            ${usecase}

            # Example
            Context:
            [
                {{
                    "name": "ballerinax/azure.openai.chat",
                    "description": "Provides a Ballerina client for the Azure OpenAI Chat API."
                }},
                {{
                    "name": "ballerinax/github",
                    "description": "Provides a Ballerina client for the GitHub API."
                }},
                {{
                    "name": "ballerinax/slack",
                    "description": "Provides a Ballerina client for the Slack API."
                }},
                {{
                    "name": "ballerinax/http",
                    "description": "Allows to intract with HTTP services."
                }}

            ]
            Question: 
            Write an application to read github issue, summarize them and post the summary to a slack channel.

            Response: 
            {{
                "libraries": ["ballerinax/github", "ballerinax/slack", "ballerinax/azure.openai.chat"]
            }} 
            """
         ),
    ]
    library_response = llm.invoke(messages)
    library_list = library_response.content

    return json.loads(library_list)


def load_minified_libraries(context_file, libs_file, libraries):
    data = pull_central(context_file, libs_file)

    minified_libraries = []
    for lib in data:

        if lib.get("name") in libraries:

            minified_lib = {
                "name": lib.get("name", ""),
                "description": lib.get("description", ""),
                "clients": [],
                "functions": []
            }
            # Process clients
            for client in lib.get("clients", []):
                minified_client = {
                    "name": client.get("name", ""),
                    "description": client.get("description", ""),
                    "functions": []
                }
                for func in client.get("functions", []):
                    if func.get("type") == "Resource Function":
                        minified_client["functions"].append({
                            "accessor": func.get("accessor", ""),
                            "paths": func.get("paths", []),
                            "parameters": [p.get("name", "") for p in func.get("parameters", []) if isinstance(p, dict)],
                            "returnType": func.get("return", {}).get("type", {}).get("name", "")
                        })
                    else:
                        minified_client["functions"].append({
                            "name": func.get("name", ""),
                            "parameters": [p.get("name", "") for p in func.get("parameters", []) if isinstance(p, dict)],
                            "returnType": func.get("return", {}).get("type", {}).get("name", "")
                        })
                minified_lib["clients"].append(minified_client)

            # Process top-level functions
            for func in lib.get("functions", []):
                minified_lib["functions"].append({
                    "name": func.get("name", ""),
                    "parameters": [p.get("name", "") for p in func.get("parameters", []) if isinstance(p, dict)],
                    "returnType": func.get("return", {}).get("type", {}).get("name", "")
                })

            minified_libraries.append(minified_lib)

        else:
            continue

    return minified_libraries


def get_suggested_functions(usecase, content):
    with open("utils\prompt_funcs.md", "r") as file:
        get_lib_system_prompt = file.read()
        get_lib_system_prompt = get_lib_system_prompt.replace("<<Context>>", content)
        get_lib_user_prompt = "QUESTION\n```\n" + usecase + "\n```"
        messages = [
            (
                "system",
                f"${get_lib_system_prompt}",
            ),
            ("human",
             f"${get_lib_user_prompt}"
             )
        ]
        llm_response = llm.invoke(messages)
        parser = JsonOutputParser()
        parsed_response = parser.parse(llm_response.content)
        suggested_function = {
            "name": parsed_response["name"],
            "clients": parsed_response["clients"]
        }

        if "functions" in parsed_response:
            suggested_function["functions"] = parsed_response["functions"]

        return suggested_function


def get_bulk_functions(usecase, library_list):
    get_lib_system_prompt = "You are an assistant tasked with selecting the Ballerina functions needed to answer a specific question from given libraries provided in the context as a JSON.  RESPOND ONLY WITH A JSON."
    get_lib_user_prompt = f"""
Context Format: A JSON array where each element represents a library with its name, clients, and functions. Each client within a library includes functions which may be of types: Remote Function, or Resource Function.

# Library Context JSON
${library_list}
# QUESTION
${usecase}

Output Format: A JSON array under the key "libraries" where each element includes only those libraries, clients, and functions that are necessary for the specified use case. Simplify the function details based on the function type:

Remote Function: Include only the function name as object. 
Resource Function: Include the accessor and paths object. Do not change the contents of the paths object.

Steps:
1. Read the Library details given in the context and the question carefully. 
2. From the given libraries in the context, Identify the libraries and their respective clients necessary for the question.
3. For each selected client include other functions based on their relevance to the question and simplify the function details as per the Output format instructions.
"""
    messages = [
        (
            "system",
            f"{get_lib_system_prompt}",
        ),
        ("human",
         f"{get_lib_user_prompt}"
         )
    ]

    llm_response = llm.invoke(messages)
    parser = JsonOutputParser()
    parsed_response = parser.parse(llm_response.content)
    return parsed_response["libraries"]

def get_library_by_name(name):
    context = pull_central(context_json,libs_json)
    for lib in context:
        if lib.get("name") == name:
            return lib


def get_client_by_name(name, clients):
    for cli in clients:
        if cli["name"] == name:
            return cli

def get_constructor(complete_function):
    for func in complete_function:
        if func["type"] == "Constructor":
            return func

def get_complete_func_for_mini_func(mini_func, full_func):
    if "name" in mini_func:
        for func in full_func:
            if "name" in func:
                if func["name"] == mini_func["name"]:
                    return func
    elif "accessor" in mini_func:
        for func in full_func:
            if "accessor" in func:
                if func["accessor"] == mini_func["accessor"] and func["paths"] == mini_func["paths"]:
                    return func


def select_clients(complete_clients, min_function_resp):
    clients = min_function_resp.get("clients")
    if len(clients) == 0:
        return []

    new_clients = []
    for min_client in clients:
        complete_client = get_client_by_name(min_client["name"], complete_clients)
        functions = min_client["functions"]
        output = []
        complete_functions = complete_client["functions"]

        if len(functions) > 0:
            constructor = get_constructor(complete_functions)
            if constructor is not None:
                output.append(constructor)

        for func in functions:
            output.append(get_complete_func_for_mini_func(func, complete_functions))

        complete_client["functions"] = output
        new_clients.append(complete_client)

    return new_clients



def select_function(complete_function, min_function_resp):
    functions_result = None
    if "functions" in min_function_resp:
        functions_result = min_function_resp["functions"]
        if len(functions_result) == 0:
            return None

    output = []
    if functions_result is not None:
        for func in functions_result:
            func_name = func["name"]
            if complete_function is None:
                return None
            for item in complete_function:
                if item["name"] == func_name:
                    output.append(item)

    return output

def is_ignored_record_name(record_name):
    ignored_records = ["CodeScanningAnalysisToolGuid", "AlertDismissedAt", "AlertFixedAt", "AlertAutoDismissedAt", "NullableAlertUpdatedAt", "ActionsCanApprovePullRequestReviews","CodeScanningAlertDismissedComment", "ActionsEnabled", "PreventSelfReview", "SecretScanningAlertResolutionComment",
    "Conference_enum_update_status", "Message_enum_schedule_type", "Message_enum_update_status", "Siprec_enum_update_status", "Stream_enum_update_status"]

    if record_name in ignored_records:
        return True
    else:
        return False

def get_typedef_by_name(name, records):
    for rec in records:
        if rec["name"] == name:
            return rec
    return Exception(f"TypeDef not found {name}")

def add_internal_record(param_type, own_records, all_records):
    if "links" not in param_type:
        return None

    links = param_type["links"]

    for link in links:
        if link["category"] == "internal":
            if is_ignored_record_name(link["recordName"]):
                continue

            own_records[link["recordName"]] = get_typedef_by_name(link["recordName"], all_records)

def contains_only_and_all_allowed_fields(dictionary, allowed_fields):
    return set(dictionary.keys()) == set(allowed_fields)


def get_own_record_refs(functions, all_typedefs):
    own_records = {}
    for func in functions:
        if func is not None:
            parameters = func["parameters"]
            for param in parameters:
                param_type = param["type"]
                add_internal_record(param_type, own_records, all_typedefs)

            return_result = func["return"]
            param_type = return_result["type"]
            add_internal_record(param_type, own_records, all_typedefs)

    own_records_values = list(own_records.values())
    for rec in own_records_values:
        if contains_only_and_all_allowed_fields(rec, ["name", "description", "type", "fields"]):
            fields = rec["fields"]
            for fie in fields:
                param_type = fie["type"]
                add_internal_record(param_type, own_records, all_typedefs)

    return own_records.values()


def get_own_typedefs_for_lib(clients, functions, all_records):
    all_functions = []
    for cli in clients:
        client_funcs = cli["functions"]
        for i in client_funcs:
            all_functions.append(i)

    if functions is not None:
        for func in functions:
            if "name" in func:
                all_functions.append(func)

    return get_own_record_refs(all_functions, all_records)

def add_library_records(external_records, library_name, rec_name):
    if library_name in external_records:
        external_records[library_name].append(rec_name)
    else:
        external_records[library_name] = [rec_name]

def get_ref_lib_name(link):
    if "libraryName" in link:
        linked_lib = link["libraryName"]
        return linked_lib
    raise Exception("Linked library name not found for external record reference")


def add_external_record(param_type, external_records):
    if "links" not in param_type:
        return None

    links = param_type["links"]
    for link in links:
        if link["category"] == "external":
            add_library_records(external_records, get_ref_lib_name(link), link["recordName"])


def get_external_type_def_refs(external_records, functions, all_typedefs):
    for func in functions:
        if func is not None:
            parameters = func["parameters"]
            for param in parameters:
                param_type = param["type"]
                add_external_record(param_type, external_records)

            return_result = func["return"]
            param_type = return_result["type"]
            add_external_record(param_type, external_records)

    if all_typedefs is not None:
        for rec in all_typedefs:
            if "fields" in rec:
                fields = rec["fields"]
                for fie in fields:
                    param_type = fie["type"]
                    add_external_record(param_type, external_records)

    return external_records


def get_external_type_descs_refs(libraries):
    external_records = {}

    for lib in libraries:
        all_functions = []
        for cli in lib["clients"]:
            client_funcs = cli["functions"]
            for i in client_funcs:
                all_functions.append(i)

        functions = lib["functions"]

        if functions is not None:
            for func in functions:
                if "name" in func:
                    all_functions.append(func)

        external_records = get_external_type_def_refs(external_records, all_functions, lib["typeDefs"])

    return external_records

def get_new_library_by_name(name, libraries):
    for lib in libraries:
        if lib["name"] == name:
            return lib

    return None

def get_new_typedef_by_name(name, records):
    for rec in records:
        if rec["name"] == name:
            return rec

    return None

def validate_typedef_fields(new_record_by_name,typedef_base_fields,typedef_other_fields):

    if new_record_by_name is None:
        return False

    if not isinstance(new_record_by_name, dict):
        return False

    record_keys = set(new_record_by_name.keys())

    if record_keys.issubset(typedef_base_fields):
        return True

    base_fields_present = record_keys.intersection(typedef_base_fields)
    other_fields_present = record_keys.intersection(typedef_other_fields)

    if base_fields_present == set(typedef_base_fields) and len(other_fields_present) == 1:
        return True

    return False


def get_external_records(new_libraries, lib_refs):
    for lib_name in lib_refs.keys():
        if lib_name.startswith("ballerina/lang.int"):
            continue

        library = get_library_by_name(lib_name)
        record_names = lib_refs.get(lib_name)

        for record_name in record_names:
            rec = get_typedef_by_name(record_name, library["typeDefs"])
            new_library_by_name = get_new_library_by_name(lib_name, new_libraries)

            if new_library_by_name is None:
                new_library = {
                    "name": lib_name,
                    "description": library["description"],
                    "clients": [],
                    "functions": [],
                    "typeDefs": [rec]
                }
                new_libraries.append(new_library)
            else:
                new_library = new_library_by_name
                typedefs = new_library["typeDefs"]
                new_record_by_name = get_new_typedef_by_name(record_name, typedefs)
                if validate_typedef_fields(new_record_by_name,["name", "description", "type"],["fields", "members", "functions"]):
                    continue
                else:
                    typedefs.append(rec)



def to_maximized_libraries(selected_libraries):
    minifized_libraries_without_records = []
    for minified_selected_lib in selected_libraries:
        full_def_of_selected_lib = get_library_by_name(minified_selected_lib["name"])
        filtered_clients = select_clients(full_def_of_selected_lib["clients"], minified_selected_lib)
        filtered_functions = select_function(full_def_of_selected_lib["functions"], minified_selected_lib) if "functions" in full_def_of_selected_lib else None

        minifized_libraries_without_records.append(
            {
                "name": full_def_of_selected_lib["name"],
                "description": full_def_of_selected_lib["description"],
                "clients": filtered_clients,
                "functions": filtered_functions,
                "typeDefs":  list(get_own_typedefs_for_lib(filtered_clients, filtered_functions, full_def_of_selected_lib["typeDefs"]))
            }
        )

    external_records_refs = get_external_type_descs_refs(minifized_libraries_without_records)
    get_external_records(minifized_libraries_without_records, external_records_refs)
    return minifized_libraries_without_records



def get_central_api_docs(usecase):

    libraries_list = get_libraries(usecase, context_json, libs_json)

    minified_func_list = load_minified_libraries(context_json, libs_json, libraries_list['libraries'])

    large_libs = []
    for lib in minified_func_list:
        count = 0
        for client in lib["clients"]:
            count += len(client["functions"])
        if count >= 100:
            large_libs.append(lib)

    for lib in large_libs:
        minified_func_list.remove(lib)


    suggested_functions = []
    for lib in large_libs:
        suggested_function = get_suggested_functions(usecase, str(lib))
        suggested_functions.append(suggested_function)

    collective_response = []
    if len(minified_func_list) != 0:
        bulk_functions = get_bulk_functions(usecase, minified_func_list)
        collective_response = bulk_functions

    for lib in suggested_functions:
        collective_response.append(lib)

    maximized_libraries = to_maximized_libraries(collective_response)
    for lib in maximized_libraries:
        lib["library_link"] = library_links[lib["name"]]

    return maximized_libraries


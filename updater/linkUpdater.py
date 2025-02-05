def get_doc_link(filename,header=None):
    filename_partition = filename.split("/")

    if filename_partition[1] == "other":
        return ""

    if filename_partition[0] == "examples":
        basepath = "https://ballerina.io/learn/by-example/"
        if filename_partition[-1].endswith(".md"):
            filename_partition[-1] = (filename_partition[-1][:-3]).replace("_", "-")

        final_path = basepath + filename_partition[-1]

        if header is not None:
            header2 = (header.replace(" ", "-").replace('``', "").replace("`", "")).lower()
            final_path = final_path + "/#" + header2

        return final_path

    if "vs-code-extension" in filename_partition:
        basepath = "https://ballerina.io/learn/vs-code-extension"
        basepath_end_index = filename_partition.index("vs-code-extension")
        elements_to_append = filename_partition[basepath_end_index + 1:]
        if elements_to_append[-1].endswith(".md"):
            elements_to_append[-1] = elements_to_append[-1][:-3]

        final_path = basepath
        for path in elements_to_append:
            final_path = final_path + f"/{path}"

        if header is not None:
            header2 = (header.replace(" ", "-").replace('``', "").replace("`", "")).lower()
            final_path = final_path + "/#" + header2

        return final_path

    if len(filename_partition) <= 4:
        basepath = "https://ballerina.io/learn/"
        if "why-ballerina" in filename_partition:
            basepath = "https://ballerina.io/why-ballerina/"
            filename_without_extension = filename_partition[-1][:-3]
            final_path = basepath + filename_without_extension

            if header is not None:
                header2 = (header.replace(" ", "-").replace('``', "").replace("`", "")).lower()
                final_path = final_path + "/#" + header2

            return final_path

        if filename_partition[1] == "integration-tutorials":
            basepath = "https://ballerina.io/learn/integration-tutorials/"
            filename_without_extension = filename_partition[-1][:-3]
            final_path = basepath + filename_without_extension
            if header is not None:
                header2 = (header.replace(" ", "-").replace('``', "").replace("`", "")).lower()
                final_path = final_path + "/#" + header2

            return final_path

        filename_without_extension = filename_partition[-1][:-3]
        final_path = basepath + filename_without_extension

        if header is not None:
            header2 = (header.replace(" ", "-").replace('``', "").replace("`", "")).lower()
            final_path = final_path + "/#" + header2

        return final_path

    else:
        basepath = "https://ballerina.io/learn/"
        filename_without_extension = filename_partition[-1][:-3]
        final_path = basepath + f"{filename_partition[-2]}/{filename_without_extension}"

        if header is not None:
            header2 = (header.replace(" ", "-").replace('``', "").replace("`", "")).lower()
            final_path = final_path + "/#" + header2

        return final_path

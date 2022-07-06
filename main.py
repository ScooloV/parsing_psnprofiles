from simple_parser import simple_parser


def main():
    file_obj = open("list_to_parse.txt", 'r')
    list_raw = file_obj.readlines()

    for list_elem in list_raw:
        elements = 99999
        if len(list_elem.split()) != 1:
            elements = int(list_elem.split()[1])

        local_parser = simple_parser(list_elem.split()[0], elements)
        local_parser.parse()

    file_obj.close()

main()

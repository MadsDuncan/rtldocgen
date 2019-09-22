#!/usr/bin/env python3

import sys
import hdlConvertor
import pypandoc

TYPE_BIT = ('std_logic', 'std_ulogic', 'boolean')
TYPE_VECT = ('std_logic_vector', 'std_ulogic_vector', 'signed', 'unsigned')
TYPE_INT = ('integer', 'real')


class System:
    def __init__(self):
        self.name = ''
        self.entities = []


class Entity:
    def __init__(self):
        self.name = ''
        self.generics = []
        self.ports = []


class EntityObj:
    def __init__(self):
        self.name = ''
        self.type = ''
        self.value = ''
        self.range = ''

    def __repr__(self):
        return '{} - {} {} {}'.format(self.name, self.type, self.range, self.value)


class Generic(EntityObj):
    pass


class Port(EntityObj):

    def __init__(self):
        super().__init__()
        self.direction = ''

    def __repr__(self):
        return super().__repr__() + ' {}'.format(self.direction)


def unpack_ent_obj(ent_obj):
    """Unpacks an hdlConvertor "entity object".

    Unpacks an "entity object" (either generic or port object)
    from the format given by hdlConvertor to an object based mapping.

    Args:
        ent_obj: A generic or port of an entity

    Returns:
        An EntityObject, either a Generic object or a Port object.

    TODO:
        Range of integer like types (like "range 0 to 15) is not passed
        correctly by hdlConvertor. Range ['NA', 'NA'] is returned.
    """

    # Check if port or generic; normalize path.
    if 'direction' in ent_obj:
        eo = Port()
        eo.direction = ent_obj['direction'].lower()
        ent_obj = ent_obj['variable']
    else:
        eo = Generic()

    eo.name = ent_obj['name']

    # Objects without range
    if not 'binOperator' in ent_obj['type']:
        for obj_type in TYPE_BIT:
            if obj_type == ent_obj['type']['literal']['value']:
                eo.type = obj_type

        for obj_type in TYPE_VECT:
            if obj_type == ent_obj['type']['literal']['value']:
                eo.type = obj_type

        for obj_type in TYPE_INT:
            if obj_type == ent_obj['type']['literal']['value']:
                eo.type = obj_type

        if ent_obj['value']:
            eo.value = ent_obj['value']['literal']['value']

    # Objects with range
    else:
        for obj_type in TYPE_VECT:
            if obj_type == ent_obj['type']['binOperator']['op0']['literal']['value']:
                eo.type = obj_type
                obj_range = ent_obj['type']['binOperator']['op1']['binOperator']
                eo.range = [obj_range['op0']['literal']['value'],
                            obj_range['op1']['literal']['value']]

        for obj_type in TYPE_INT:
            if obj_type == ent_obj['type']['binOperator']['op0']['literal']['value']:
                eo.type = obj_type
                eo.range = ['NA', 'NA']

    # Set value if available
    if ent_obj['value']:
        eo.value = ent_obj['value']['literal']['value']

        if eo.range == '':
            if eo.type in TYPE_VECT:
                eo.range = [ent_obj['value']['literal']['bits'] - 1, 0]

    return eo


def read_vhdl(rtl_file):
    """Reads and parses a VHDL file.

    The system is mapped from hdlConvertor format to a object based format,
    containing all entities of the file.

    Args:
        rtl_file: The name and path of a file containgen VHDL code to be documented.

    Returns:
        A System object containing a list of all entities in rtl_file.
    """

    objs = hdlConvertor.parse(rtl_file, 'vhdl')
    syst = System()

    for entity in objs['entities']:
        ent = Entity()
        ent.name = entity['name']

        for generic in entity['generics']:
            g = unpack_ent_obj(generic)
            ent.generics.append(g)
            print(g)

        for port in entity['ports']:
            p = unpack_ent_obj(port)
            ent.ports.append(p)
            print(p)

        syst.entities.append(ent)

    return syst


def gen_vhdl_doc(syst):
    """Generates documentation for a VHDL system.

    Generates a markdown file with tables of each entity of syst.
    The markdown file is converted to .pdf and .odt.

    Args:
        syst: A System object containing a list of entities.

    TODO:
        Find a method to export colored things to .odt format.
        As it is now, colored text disappears in .odt format.
    """

    doc = (
        '---\n'
        'title: title here!\n'
        'header-includes: |\n'
        '    \\usepackage{xcolor}\n'
        '---\n\n'
    )

    doc += 'This should be \\textcolor{blue}{blue} text.\n\n'

    for entity in syst.entities:

        doc += '# {} component overview\n\n'.format(entity.name)

        doc += (
            '## Generic overview\n\n'
            '|name|type|range|default value|\n'
            '|-|-|-|-|\n'
        )

        for generic in entity.generics:

            # Format range
            g_range = ''
            if generic.range:
                if generic.type in TYPE_VECT:
                    g_range = '{}:{}'.format(
                        generic.range[0], generic.range[1])
                elif generic.type in TYPE_INT:
                    g_range = '{}-{}'.format(
                        generic.range[0], generic.range[1])

            # Format value
            g_value = generic.value
            if generic.value:
                if generic.type in ['std_logic_vector', 'std_ulogic_vector']:
                    g_value = hex(generic.value)

            # Add row
            doc += '|{}|{}|{}|{}|\n'.format(generic.name,
                                            generic.type, g_range, g_value)

        doc += (
            '## Port overview\n\n'
            '|name|direction|type|range|default value|\n'
            '|-|-|-|-|-|\n '
        )

        for port in entity.ports:

            # Format range
            p_range = ''
            if port.type in TYPE_VECT:
                p_range = '{}:{}'.format(port.range[0], port.range[1])
            elif port.type in TYPE_INT:
                p_range = '{}-{}'.format(port.range[0], port.range[1])

            # Add row
            doc += '|{}|{}|{}|{}|{}|\n'.format(port.name, port.direction,
                                               port.type, p_range, port.value)

    with open(file_name + '.md', 'w') as docfile:
        docfile.write(doc)

    pypandoc.convert_file(file_name + '.md', 'odt', outputfile=file_name + '.odt')
    pypandoc.convert_file(file_name + '.md', 'pdf', outputfile=file_name + '.pdf')


if __name__ == '__main__':

    if len(sys.argv) != 2:
        raise ValueError('Incorrect number of CL arguments.')

    with open(sys.argv[1], 'r') as fp:
        code = fp.read

    file_name = sys.argv[1].split('.')[0]
    file_extension = sys.argv[1].split('.')[-1]
    file_extension = file_extension.lower()

    if file_extension == 'vhd' or file_extension == 'vhdl':
        print('vhdl file!')
        gen_vhdl_doc(read_vhdl(sys.argv[1]))

    elif file_extension == 'v':
        print('verilog file!')
        NotImplementedError('Verilog documentation generation not implemented.')

    else:
        ValueError('no or incorrect file extention')

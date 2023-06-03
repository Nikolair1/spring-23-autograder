code = ['tclass', 'node', ['field_type'], ['field', 'node@field_type', 'next', 'null'], ['field', 'field_type', 'value'], ['method', 'void', 'set_val', [['field_type', 'v']], ['set', 'value', 'v']], ['method', 'field_type', 'get_val', [], ['return', 'value']], ['method', 'void', 'set_next', [['node@field_type', 'n']], ['set', 'next', 'n']], ['method', 'node@field_type', 'get_next', [], ['return', 'next']]]
actual_types = ['int']


def create_class_def_from_template(class_name,actual_types):
        code = ['tclass', 'node', ['field_type'], ['field', 'node@field_type', 'next', 'null'], ['field', 'field_type', 'value'], ['method', 'void', 'set_val', [['field_type', 'v']], ['set', 'value', 'v']], ['method', 'field_type', 'get_val', [], ['return', 'value']], ['method', 'void', 'set_next', [['node@field_type', 'n']], ['set', 'next', 'n']], ['method', 'node@field_type', 'get_next', [], ['return', 'next']]]
        code[0] = "class"
        field_replacements = dict(zip(code[2], actual_types))
        code = replace_fields(code, field_replacements)
        code.pop(2)
        code[1] = class_name
        print(code)
        
        

def replace_fields(template, replacements):
    if isinstance(template, list):
        return [replace_fields(item, replacements) for item in template]
    elif isinstance(template, str):
        # Split and replace only if template is a string
        if '@' in template:
            type_name, field = template.split('@')
            return '@'.join([type_name, replacements.get(field, field)])
        else:
            return replacements.get(template, template)
    else:
        return template
    
create_class_def_from_template("node",actual_types)

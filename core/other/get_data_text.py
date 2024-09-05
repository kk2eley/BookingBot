def line_dict(dicts):
    result = []

    def list_dict(dicts):
        for key, val in dicts.items():
            if isinstance(val, dict):
                list_dict(val)
            else:
                result.append(f'{key.capitalize()}: {val}')

    list_dict(dicts)
    return ';\r\n'.join(result)

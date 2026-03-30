def move_to_position(target, key, position):
    target = target.copy()
    value = target.pop(key)
    item = {key: value}

    items = list(target.items())

    items = items[:position] + list(item.items()) + items[position:]

    target = dict(items)
    return target

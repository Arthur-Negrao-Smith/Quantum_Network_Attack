def choiceNode(nodes: list, choice_node: int = None) -> list:
    """
        It will choose one of the network nodes according to the 
        chosen and random number if it does not determine a node
    """
    choice_node = choice_node
    if choice_node == None:
        from random import randint
        choice_node = randint(0, len(nodes) - 1)
    
    if len(nodes) - choice_node == 2:
        aux = [nodes[choice_node], nodes[choice_node + 1], nodes[0]]
        print(f"Caso == 2: {aux}")
        return aux
    elif len(nodes) - choice_node == 1:
        aux = [nodes[choice_node], nodes[0], nodes[1]]
        print(f"Caso == 1: {aux}")
        return aux
    else:
        aux = [nodes[choice_node], nodes[choice_node+1], nodes[choice_node+2]]
        print(f"Caso genérico: {aux}")
        return aux

if __name__ == '__main__':
    nodes = ['r0', 'r1', 'r2', 'r3']
    aux = choiceNode(nodes)

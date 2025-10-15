# Import =========================================================================================================
import uuid

import logging

from collections import defaultdict

from typing import List, Dict, Tuple

import re

import streamlit as st

# Fonctions =========================================================================================================
logger = logging.getLogger("MyLogger")
logger.setLevel(logging.INFO)

class Node:
    def __init__(self, name:str, node_class:str=None, properties:dict=None):
        self.Name = name
        self.Node_class = node_class if node_class else "default"
        self.Properties = properties if properties else {}
        self.Id = self.generate_id()
        self.Neighbours = set()
        self.HUB = False
    def generate_id(self)->str:
        return f"{self.Node_class}:{self.Name}:{uuid.uuid4()}"
    def add_neighbour(self, neighbour_id:str):
        self.Neighbours.add(neighbour_id)
    def remove_neighbour(self, neighbour_id):
        self.Neighbours.discard(neighbour_id)
    def __str__(self)->str:
        return f"Node(name={self.Name}, class={self.Node_class}, id={self.Id}, neighbours={list(self.Neighbours)})"
    
class Edge:
    def __init__(self, source_id:str, target_id:str, node_class:str=None, properties:dict=None):
        self.Source_id = source_id
        self.Target_id = target_id
        self.Edge_class = node_class if node_class else "default"
        self.Properties = properties if properties else {}
        self.Id = self.generate_id()
    def generate_id(self)->str:
        return f"{self.Source_id}->{self.Target_id}:{uuid.uuid4()}"    
    def __str__(self)->str:
        return f"Edge(source={self.Source_id}, target={self.Target_id}, class={self.Edge_class}, id={self.Id})"

class OneRingDB:
    def __init__(self):
        self.NodeDictionary = {}
        self.EdgeDictionary = {}
        self.Name2Nodes:Dict[str:List[Node]] = defaultdict(list)
        self.SourceTargetNames2Edge:Dict[Tuple[str, str]:Edge] = {}

    # CREATOR =========================================================================================================
    def create_node(self, name:str, node_class:str=None, properties:dict=None)->str:
        node = Node(name, node_class, properties)
        self.NodeDictionary[node.Id] = node
        self.Name2Nodes[name].append(node)
        return node.Id
    def create_edge(self, source_id:str, target_id:str, edge_class=None, properties=None)->str:
        if source_id not in self.NodeDictionary or target_id not in self.NodeDictionary:
            raise ValueError("Les nœuds source et cible doivent exister dans la base de données.")
        edge = Edge(source_id, target_id, edge_class, properties)
        self.EdgeDictionary[edge.Id] = edge
        self.NodeDictionary[source_id].add_neighbour(target_id)
        self.NodeDictionary[target_id].add_neighbour(source_id)
        self.SourceTargetNames2Edge[(self.get_node_by_id(source_id).Name, self.get_node_by_id(target_id).Name)] = edge
        return edge.Id
    
    # GETTER ==========================================================================================================
    def get_node_by_id(self, node_id:str)->Node:
        if node_id not in self.NodeDictionary:
            raise ValueError("Le nœud recherché, Id {node_id}, ne figure pas dans la base de données.")
        return self.NodeDictionary.get(node_id)
    def get_edge_by_id(self, edge_id:str)->Edge:
        if edge_id not in self.EdgeDictionary:
            raise ValueError("L'arête recherchée ne figure pas dans la base de données.")
        return self.EdgeDictionary.get(edge_id)
    def get_node_by_name(self, node_name:str, find_single_node=True):
        """Si find_single_node == False, retournez une liste de Node débutant de `node_name`"""
        if find_single_node:
            for name in self.Name2Nodes:
                if name == node_name:
                    if self.Name2Nodes[node_name]:
                        return self.Name2Nodes[node_name][0]
                    else:
                        raise ValueError(f"Le nœud recherché {node_name} ne figure pas dans la base de données.")
        else:
            founded_nodes = []
            for name in self.Name2Nodes:
                if name.startswith(node_name):
                    founded_nodes += self.Name2Nodes[name]
            if founded_nodes:
                return founded_nodes
            raise ValueError(f"Le nœud recherché {node_name} ne figure pas dans la base de données.")
    def get_nodes_by_class(self, class_name:str, condition=None)->List[Node]:
        """Retournez les Node de telle classe avec telles conditions. Les conditions AND sont en dictionnaire, tandis que les conditions OR sont en liste"""
        if not condition:
            return [node for node in self.NodeDictionary.values() if node.Node_class == class_name]
        else:
            nodes_to_return = []
            if type(condition) is dict:
                for node in self.NodeDictionary.values():
                    if node.Node_class == class_name:
                        flag = True
                        for key, value in condition.items():
                            if key not in node.Properties:
                                flag = False
                            else:
                                if node.Properties[key] != value:
                                    flag = False
                        if flag:
                            nodes_to_return.append(node)
            elif type(condition) is list:
                for node in self.NodeDictionary.values():
                    if node.Node_class == class_name:
                        for c in condition:
                            flag = True
                            for key, value in c.items():
                                if key not in node.Properties:
                                    flag = False
                                else:
                                    if node.Properties[key] != value:
                                        flag = False
                            if flag:
                                nodes_to_return.append(node)
            return nodes_to_return
    def get_nodes_by_HUB(self, condition=None)->List[Node]:
        """Retournez les Hubs avec telles conditions. Les conditions AND sont en dictionnaire, tandis que les conditions OR sont en liste"""
        if not condition:
            return [node for node in self.NodeDictionary.values() if node.HUB]
        else:
            nodes_to_return = []
            if type(condition) is dict:
                for node in self.NodeDictionary.values():
                    if node.HUB:
                        flag = True
                        for key, value in condition.items():
                            if key not in node.Properties:
                                flag = False
                            else:
                                if node.Properties[key] != value:
                                    flag = False
                        if flag:
                            nodes_to_return.append(node)
            elif type(condition) is list:
                for node in self.NodeDictionary.values():
                    if node.HUB:
                        for c in condition:
                            flag = True
                            for key, value in c.items():
                                if key not in node.Properties:
                                    flag = False
                                else:
                                    if node.Properties[key] != value:
                                        flag = False
                            if flag:
                                nodes_to_return.append(node)
            return nodes_to_return
    def get_all_nodes(self, condition=None):
        """Retounrez tous les Node avec telles conditions. Les conditions AND sont en dictionnaire, tandis que les conditions OR sont en liste"""
        if not condition:
            return list(self.NodeDictionary.values())
        else:
            nodes_to_return = []
            if type(condition) is dict:
                for node in self.NodeDictionary.values():
                    flag = True
                    for key, value in condition.items():
                        if key not in node.Properties:
                            flag = False
                        else:
                            if node.Properties[key] != value:
                                flag = False
                    if flag:
                        nodes_to_return.append(node)
            elif type(condition) is list:
                for node in self.NodeDictionary.values():
                    for c in condition:
                        flag = True
                        for key, value in c.items():
                            if key not in node.Properties:
                                flag = False
                            else:
                                if node.Properties[key] != value:
                                    flag = False
                        if flag:
                            nodes_to_return.append(node)
            return nodes_to_return
    def get_edge_by_nodes_names(self, source_name:str, target_name:str)->Edge:
        """Retounez l'edge selon les noms source et cible."""
        if (source_name, target_name) not in self.SourceTargetNames2Edge:
            raise ValueError(f"L'arête recherchée entre {source_name} et {target_name}ne figure pas dans la base de données.")
        return self.SourceTargetNames2Edge[(source_name, target_name)]
    def get_edges_by_class(self, edge_class_name:str, condition=None)->List[Edge]:
        """Retounrez les Edge de telle classe avec telles conditions. Les conditions AND sont en dictionnaire, tandis que les conditions OR sont en liste"""
        if not condition:
            return [edge for edge in self.EdgeDictionary.values() if edge.Edge_class == edge_class_name]
        else:
            edges_to_return = []
            if type(condition) is dict:
                for edge in self.EdgeDictionary.values():
                    if edge.Edge_class == edge_class_name:
                        flag = True
                        for key, value in condition.items():
                            if key not in edge.Properties:
                                flag = False
                            else:
                                if edge.Properties[key] != value:
                                    flag = False
                        if flag:
                            edges_to_return.append(edge)

            elif type(condition) is list:
                for edge in self.EdgeDictionary.values():
                    if edge.Edge_class == edge_class_name:
                        for c in condition:
                            flag = True
                            for key, value in c.items():
                                if key not in edge.Properties:
                                    flag = False
                                else:
                                    if edge.Properties[key] != value:
                                        flag = False
                            if flag:
                                edges_to_return.append(edge)
            return edges_to_return
        
    def get_edge_by_class_and_nodes_names(self, edge_class_name:str, source_name:str, target_name:str)->Edge:
        """Retournez les Edge de telle classe ayant tel nœud source et tel nœud cible."""
        if (source_name, target_name) not in self.SourceTargetNames2Edge:
            raise ValueError(f"L'arête recherchée entre {source_name} et {target_name} ne figure pas dans la base de données.")
        for edge in self.EdgeDictionary.values():
            if edge.Edge_class == edge_class_name and self.get_node_by_id(edge.Source_id).Name == source_name and self.get_node_by_id(edge.Target_id).Name == target_name:
                return edge
    def get_all_edges(self, condition=None):
        """Retournez tous les Edge avec telles conditions. Les conditions AND sont en dictionnaire, tandis que les conditions OR sont en liste"""
        if not condition:
            return list(self.EdgeDictionary.values())
        else:
            edges_to_return = []
            if type(condition) is dict:
                for edge in self.EdgeDictionary.values():
                    flag = True
                    for key, value in condition.items():
                        if key not in edge.Properties:
                            flag = False
                        else:
                            if edge.Properties[key] != value:
                                flag = False
                    if flag:
                        edges_to_return.append(edge)
            elif type(condition) is list:
                for edge in self.EdgeDictionary.values():
                    for c in condition:
                        flag = True
                        for key, value in c.items():
                            if key not in edge.Properties:
                                flag = False
                            else:
                                if edge.Properties[key] != value:
                                    flag = False
                        if flag:
                            edges_to_return.append(edge)
            return edges_to_return

    
    # SETTER ==========================================================================================================
    def update_node(self, node_id:str, key:str, value):
        
        logger.handlers.clear()
        logger.addHandler(logging.StreamHandler())
        
        # Vérifier si le nœud existe
        node = self.NodeDictionary.get(node_id)
        if not node:
            raise ValueError("Le nœud à modifier ne figure pas dans la base de données.")
        
        current_node_name = node.Name

        # Trouver l'index du nœud dans Name2Nodes        
        current_node_in_Name2Nodes_index = -1
        for idx, node in enumerate(self.Name2Nodes[current_node_name]):
            if node.Id == node_id:
                current_node_in_Name2Nodes_index = idx
        key = key.lower()
        
        # Mettre à jour le nom du nœud
        if key.startswith("name") and isinstance(value, str):
            node.Name = value
            self.Name2Nodes[current_node_name].pop(current_node_in_Name2Nodes_index)
            self.Name2Nodes[value].append(node)
            logger.info(f"Le nom du nœud '{current_node_name}' a été changé en '{value}'.")
            # Update le node dans les edges
            edges_to_update = list(self.SourceTargetNames2Edge.keys())
            for source_name, target_name in edges_to_update:
                edge = self.SourceTargetNames2Edge.pop((source_name, target_name))
                if current_node_name in source_name:
                    self.SourceTargetNames2Edge[(value, target_name)] = edge
                elif current_node_name in target_name:
                    self.SourceTargetNames2Edge[(source_name, value)] = edge

        # Mettre à jour la classe du nœud
        elif key.startswith("class") and isinstance(value, str):
            node.node_class = value
            self.Name2Nodes[current_node_name][current_node_in_Name2Nodes_index].Node_class = value
            logger.info(f"La classe du nœud '{current_node_name}' a été changé en '{value}'.")

        # Mettre à jour les propriétés du nœud
        elif key.startswith("propert") and isinstance(value, dict):
            for k, v in value.items():
                old_value = node.Properties.get(k)
                node.Properties[k] = v
                if old_value is not None:
                    logger.info(f"La propriété '{k}' de '{current_node_name}' a été changée de '{old_value}' à '{v}'.")
                else:
                    logger.info(f"La propriété '{k}' avec valeur '{v}' a été ajoutée dans le nœud '{current_node_name}'.")
        else:
            raise ValueError("Il faut indiquer le champ du nœud à modifier entre 'name', 'class' et 'property'")
    
    def update_edge(self, edge_id: str, key: str, value):

        # Vérifier si l'arête existe
        edge = self.EdgeDictionary.get(edge_id)
        if not edge:
            raise ValueError("L'arête à modifier ne figure pas dans la base de données.")

        key = key.lower()

        # Trouver les noms des nœuds source et cible actuels
        source_node = self.NodeDictionary.get(edge.Source_id)
        target_node = self.NodeDictionary.get(edge.Target_id)
        if not source_node or not target_node:
            raise ValueError("Les nœuds de l'arête ne sont pas valides.")

        current_source_name = source_node.Name
        current_target_name = target_node.Name

        # Vérifier si l'arête est enregistrée correctement
        edge_key = (current_source_name, current_target_name)
        if edge_key not in self.SourceTargetNames2Edge:
            raise ValueError("L'arête n'est pas indexée correctement dans SourceTargetNames2Edge.")

        # Mise à jour du nœud source
        if key.startswith("source") and isinstance(value, str):
            new_source_node = self.NodeDictionary.get(value)
            if not new_source_node:
                raise ValueError("Le nouveau nœud source ne figure pas dans la base de données.")

            edge.Source_id = value
            new_key = (new_source_node.Name, current_target_name)

            # Mettre à jour SourceTargetNames2Edge
            del self.SourceTargetNames2Edge[edge_key]
            self.SourceTargetNames2Edge[new_key] = edge

            # Mettre à jour les voisins du target_node
            target_node.remove_neighbour(source_node.Id)
            target_node.add_neighbour(value)

        # Mise à jour du nœud cible
        elif key.startswith("target") and isinstance(value, str):
            new_target_node = self.NodeDictionary.get(value)
            if not new_target_node:
                raise ValueError("Le nouveau nœud cible ne figure pas dans la base de données.")

            edge.Target_id = value
            new_key = (current_source_name, new_target_node.Name)

            # Mettre à jour SourceTargetNames2Edge
            del self.SourceTargetNames2Edge[edge_key]
            self.SourceTargetNames2Edge[new_key] = edge

            # Mettre à jour les voisins du source_node
            source_node.remove_neighbour(target_node.Id)
            source_node.add_neighbour(value)

        # Mise à jour de la classe de l'arête
        elif key.startswith("class") and isinstance(value, str):
            edge.Edge_class = value
            self.SourceTargetNames2Edge[edge_key].Edge_class = value
            logger.info(f"Classe de l'arête ({current_source_name} -> {current_target_name}) changée en '{value}'.")

        # Mise à jour des propriétés de l'arête
        elif key.startswith("propert") and isinstance(value, dict):
            for k, v in value.items():
                old_value = edge.Properties.get(k)
                edge.Properties[k] = v
                if old_value is not None:
                    logger.info(f"Propriété '{k}' de l'arête ({current_source_name} -> {current_target_name}) changée de '{old_value}' à '{v}'.")
                else:
                    logger.info(f"Propriété '{k}' ajoutée à l'arête ({current_source_name} -> {current_target_name}) avec valeur '{v}'.")
        else:
            raise ValueError("Il faut indiquer le champ du nœud à modifier entre 'source', 'target', 'class' et 'property'")
        
    # DELETER =========================================================================================================
    def delete_node(self, node_id):
        if node_id not in self.NodeDictionary:
            raise ValueError("Le nœud à supprimer n'existe pas dans la base de données.")
        
        # Supprimer toutes les arêtes associées
        edges_to_delete = [edge_id for edge_id, edge in self.EdgeDictionary.items() if edge.Source_id == node_id or edge.Target_id == node_id]
        for edge_id in edges_to_delete:
            self.delete_edge(edge_id)

        # Supprimer le nœud dans Name2Nodes
        current_node_name = self.NodeDictionary[node_id].Name        
        current_node_in_Name2Nodes_index = -1
        for idx, node in enumerate(self.Name2Nodes[current_node_name]):
            if node.Id == node_id:
                current_node_in_Name2Nodes_index = idx
        self.Name2Nodes[current_node_name].pop(current_node_in_Name2Nodes_index)

        # Supprimer le nœud
        del self.NodeDictionary[node_id]
    
    def delete_edge(self, edge_id):
        if edge_id not in self.EdgeDictionary:
            raise ValueError("L'arête à supprimer n'existe pas dans la base de données.")
        
        edge = self.EdgeDictionary[edge_id]
        self.NodeDictionary[edge.Source_id].remove_neighbour(edge.Target_id)
        self.NodeDictionary[edge.Target_id].remove_neighbour(edge.Source_id)
        del self.EdgeDictionary[edge_id]
        # Supprimer également l'Edge dans SourceTargetNames2Edge
        del self.SourceTargetNames2Edge[(self.get_node_by_id(edge.Source_id).Name, self.get_node_by_id(edge.Target_id).Name)]
        
    # REPRESENTATEUR ==================================================================================================
    def __str__(self)->str:
        return f"OneRingDB(Nodes={len(self.NodeDictionary)}, Edges={len(self.EdgeDictionary)})"
    
class ORQueryParser:
    def __init__(self, query:str, base:OneRingDB):
        self.line = query
        self.Command = ""
        self.Id = ""
        self.Class = ""
        self.Properties = {}
        self.Condition = {}
        self.parseur(base)
    
    def __str__(self):
        representation = ""
        if self.Command:
            representation += self.Command + "\n"
        if self.Id:
            representation += str(self.Id) + "\n"
        if self.Class:
            representation += self.Class + "\n"
        if self.Properties:
            representation += str(self.Properties) + "\n"
        if self.Condition:
            representation += str(self.Condition) + "\n"
        return representation.strip()

    def extraire_elements(self, chaine):
        """Pour les requêtes sauf celles sur les nœuds."""
        pattern = r'\[\]|\[[^\]]+\]|"[^"]+"|\w+|='
        return re.findall(pattern, chaine)

    def extraire_node_query_elements(self, chaine):
        """Pour les requêtes sur les nœuds."""
        pattern = r'\(\)|\([^\)]+\)|"[^"]+"|\w+|='
        return re.findall(pattern, chaine)

    def check_query_line(self, line: str):
        """Vérifier une ligne de requête"""

        # Vérifier le mot clé
        line_head = line.split(' ', maxsplit=1)[0]
        valid_commands = {'UPDATE', 'READ', 'CREATE', 'DELETE', 'LINK', 'COLOR', 'CLUSTER', 'LINEARISE'}

        if line_head not in valid_commands:
            raise SyntaxError(f"{line} n'a pas une en-tête valable.")
        
        # Extraire les éléments de la requête
        if '(' in line and ')' in line:
            line_elements = self.extraire_node_query_elements(line)
        else:
            line_elements = self.extraire_elements(line)
        
        nb_line_elements = len(line_elements)

        # Requête CLUSTER
        if line_head == "CLUSTER":
            if nb_line_elements > 2:
                raise SyntaxError(f"{line} a trop d'éléments.")
            # Quand 2 éléments, seulement CLUSTER NOT est possible.
            if nb_line_elements == 2 and line_elements[-1] != 'NOT':
                raise SyntaxError(f"Utiliser NOT pour ne pas faire le clustering.")
        # Requête COLOR
        elif line_head == 'COLOR':
            if nb_line_elements > 2:
                raise SyntaxError(f"{line} a trop d'éléments.")
            # Quand 2 éléments, seulement COLOR NOT est possible.
            if nb_line_elements == 2 and line_elements[-1] != 'NOT':
                raise SyntaxError(f"Utiliser NOT pour ne pas faire le coloriage.")
        # Requête LINEARISE
        elif line_head == 'LINEARISE':
            if nb_line_elements > 2:
                raise SyntaxError(f"{line} a trop d'éléments.")
            # Quand 2 éléments, seulement LINEARISE NOT est possible.
            if nb_line_elements == 2 and line_elements[-1] != 'NOT':
                raise SyntaxError(f"Utiliser NOT pour ne pas faire le linéarisation.")
        # Requête LINK
        elif line_head == "LINK":
            if nb_line_elements > 6:
                raise SyntaxError(f"{line} a trop d'éléments.")

            if nb_line_elements > 1:
                nodes_to_look = line_elements[1]
                if not (nodes_to_look.startswith('[') and nodes_to_look.endswith(']')):
                    raise SyntaxError(f"{line} manque des crochets.")

                nodes_inner = nodes_to_look[1:-1]
                try:
                    first_node, second_node = nodes_inner.split(" ", maxsplit=1)
                except ValueError:
                    raise SyntaxError(f"La syntaxe pour représenter les deux nœuds n'est pas correcte.")

                if not first_node.endswith(","):
                    raise SyntaxError(f"Il faut un espace après le virgule.")

                if not bool(re.match(r'(?:"[^"]*"|\w+|\d+)', second_node)):
                    raise SyntaxError(f"Il ne faut pas avoir les guillemets au sein des mêmes guillemets.")

            # Quand 3 éléments, seulement ALL est possible
            if nb_line_elements == 3 and line_elements[2] != "ALL":
                raise SyntaxError(f"Vous avez oublié le mot-clé 'ALL'.")

            # Quand 4 éléments, seulement MAX_LENGTH ou MIN_LENGTH sont possibles, le 4e élément doit être un nombre
            if nb_line_elements == 4:
                if line_elements[2] != "MAX_LENGTH" and line_elements[2] != "MIN_LENGTH":
                    raise SyntaxError(f"L'erreur de syntaxe dans : {line}")
                if not line_elements[3].isdigit():
                    raise SyntaxError(f"L'erreur de syntaxe dans : {line}")
            # Quand 4 éléments, seulement MAX_LENGTH et MIN_LENGTH sont possibles, le 4e élément doit être un nombre
            if nb_line_elements == 6:
                if set(line_elements[2::2]) != set(['MAX_LENGTH', 'MIN_LENGTH']):
                    raise SyntaxError(f"L'erreur de syntaxe dans : {line}")
                if not (line_elements[3].isdigit() and line_elements[5].isdigit()):
                    raise SyntaxError(f"L'erreur de syntaxe dans : {line}")
        # Requête sur nœuds ou sur arêtes
        else:
            
            if not (('[' in line and ']' in line) or ('(' in line and ')' in line)):
                raise SyntaxError(f"L'erreur de syntaxe dans : {line}")
            # Requête sur arêtes
            if '[' in line and ']' in line:
                if nb_line_elements == 2:
                    nodes_to_look = line_elements[1]
                    if not (nodes_to_look.startswith('[') and nodes_to_look.endswith(']')):
                        raise SyntaxError(f"L'erreur de syntaxe dans : {line}")

                    inner = nodes_to_look[1:-1]
                    if line_head == "READ":
                        return bool(re.fullmatch(r"(|\w+, \w+|:\w+)", inner))
                    elif line_head == "DELETE":
                        return bool(re.fullmatch(r"(:\w+|\w+, \w+)", inner))
                    elif line_head in {"CREATE", "UPDATE"}:
                        return bool(re.match(r'^\w+, \w+:[\w_]+\{(?:\w+:(?:"[^"]*"|\w+|\d+)(?:,\s*)?)+\}$', inner))
                    

                elif nb_line_elements > 2 and 'WHERE' in line:
                    if line_head not in set(["READ", "UPDATE"]):
                        raise SyntaxError(f"L'erreur de syntaxe dans : {line}")
                    
                    if nb_line_elements < 6:
                        raise SyntaxError(f"L'erreur de syntaxe dans : {line}")

                    if 'AND' in line or 'OR' in line:
                        if not set(line_elements[4::4]) == set(['=']):
                            raise SyntaxError(f"L'erreur de syntaxe dans les conditions dans : {line}")
                    else:
                        if line_elements[2:5:2] != ['WHERE', '=']:
                            raise SyntaxError(f"L'erreur de syntaxe dans : {line}")

                    nodes_to_look = line_elements[1]
                    if not (nodes_to_look.startswith('[') and nodes_to_look.endswith(']')):
                        raise SyntaxError(f"L'erreur de syntaxe dans : {line}")
                    if line_head == "READ":
                        return bool(re.fullmatch(r"|:\w+|\w+, \w+", nodes_to_look[1:-1]))
                    elif line_head == "UPDATE":
                        return bool(re.match(r'^\w+, \w+:[\w_]+\{(?:\w+:(?:"[^"]*"|\w+|\d+)(?:,\s*)?)+\}$', nodes_to_look[1:-1]))

                else:
                    raise SyntaxError(f"L'erreur de syntaxe dans : {line}")
            # Requête sur nœuds
            if '(' in line and ')' in line:
                if nb_line_elements == 2:
                    nodes_to_look = line_elements[1]
                    if not (nodes_to_look.startswith('(') and nodes_to_look.endswith(')')):
                        raise SyntaxError(f"L'erreur de syntaxe dans : {line}")
                    inner = nodes_to_look[1:-1]
                    if line_head == "DELETE":
                        return bool(re.fullmatch(r"\w+", inner))
                    elif line_head == "READ":
                        return bool(re.fullmatch(r"(|:?\w+)", inner))
                    elif line_head == "CREATE":
                        return bool(re.match(r'^\w+:\w+\{(?:\w+:(?:"[^"]*"|\w+|\d+)(?:,\s*)?)+\}$', inner))
                    else:
                        raise SyntaxError(f"L'erreur de syntaxe dans : {line}")
                else:
                    if line_head == "READ":
                        if nb_line_elements < 6:
                            raise SyntaxError(f"L'erreur de syntaxe dans : {line}")
                        
                        if 'AND' in line or 'OR' in line:
                            if not set(line_elements[4::4]) == set(['=']):
                                raise SyntaxError(f"L'erreur de syntaxe dans les conditions dans : {line}")
                        else:
                            if line_elements[2:5:2] != ['WHERE', '=']:
                                raise SyntaxError(f"L'erreur de syntaxe dans : {line}")
                        
                        nodes_to_look = line_elements[1]
                        if not (nodes_to_look.startswith('(') and nodes_to_look.endswith(')')):
                            raise SyntaxError(f"L'erreur de syntaxe dans : {line}")

                        return bool(re.fullmatch(r"|:?\w+", nodes_to_look[1:-1]))
                    elif line_head == "UPDATE":
                        if nb_line_elements > 2:
                            if nb_line_elements < 6:
                                raise SyntaxError(f"L'erreur de syntaxe dans : {line}")
                            
                            if 'AND' in line or 'OR' in line:
                                if not set(line_elements[4::4]) == set(['=']):
                                    raise SyntaxError(f"L'erreur de syntaxe dans les conditions dans : {line}")
                            else:
                                if line_elements[2:5:2] != ['WHERE', '=']:
                                    raise SyntaxError(f"L'erreur de syntaxe dans : {line}")
                        nodes_to_look = line_elements[1]
                        if not (nodes_to_look.startswith('(') and nodes_to_look.endswith(')')):
                            raise SyntaxError(f"L'erreur de syntaxe dans : {line}")
                        # (Gandalf{Color:White})
                        return bool(re.match(r'^\w+(?:\:\w+)?\{(?:\w+:(?:"[^"]*"|\w+|\d+)(?:,\s*)?)+\}$', nodes_to_look[1:-1]))
        return True
    
    def parseur(self, base):
        """Parse une ligne de requête"""
        line = self.line
        if not self.check_query_line(line):
            raise SyntaxError(f"L'erreur de syntaxe dans : {line}")
        
        # Extraie le mot clé
        line_head = line.split(' ', maxsplit=1)[0]
        if line_head == "CLUSTER":
            line_elements = self.extraire_node_query_elements(line)
            self.Command = 'CLUSTER'
            if line_elements[-1] == 'NOT':
                self.Command += ' NOT'
            return
        if line_head == 'COLOR':
            line_elements = self.extraire_node_query_elements(line)
            self.Command = 'COLOR'
            if line_elements[-1] == 'NOT':
                self.Command += ' NOT'
            return
        if line_head == 'LINEARISE':
            line_elements = self.extraire_node_query_elements(line)
            self.Command = 'LINEARISE'
            if line_elements[-1] == 'NOT':
                self.Command += ' NOT'
            return
        # Requête sur Node
        if '(' in line:
            line_elements = self.extraire_node_query_elements(line)
            if line_head == "CREATE":
                # Command = mot clé + Node
                self.Command = line_head + " Node"
                node_name = line_elements[1][1:-1].split(':', maxsplit=1)[0]
                # Id = Node name
                self.Id = node_name
                node_class = line_elements[1][1:-1].split(':', maxsplit=1)[1].split('{', maxsplit=1)[0]
                # Class = Node class
                self.Class = node_class
                node_property_brut = line_elements[1][1:-1][len(node_name)+len(node_class)+1:]
                
                node_property = {}
                for ele in node_property_brut[1:-1].split(', '):
                    key, value = ele.split(':', maxsplit=1)
                    try:
                        node_property[key] = str(eval(value))
                    except:
                        node_property[key] = value
                # Properties = Node property
                self.Properties = node_property
            
            elif line_head == "READ":
                # Command = mot clé + Node
                self.Command = line_head + " Node"
                if line_elements[1] == '()':
                    # () = ALL pour tous les Node
                    self.Command += " ALL"
                elif line_elements[1][1:-1].startswith(':'):
                    # Commence par : = Class
                    self.Command += " CLASS"
                    class_name = line_elements[1][1:-1].split(':', maxsplit=1)[1]
                    self.Class = class_name
                else:
                    # Sinon on cherche un Node spécifique
                    self.Command += " SPECIFIC"
                    node_name = line_elements[1][1:-1]
                    self.Id = base.get_node_by_name(node_name).Id
                condition = {}
                # S'il y a encore des conditions OR ou AND...
                if 'WHERE' in line_elements:
                    # Pour les conditions AND
                    if 'OR' not in line_elements[5:]:
                        keys = line_elements[3::4]
                        values = line_elements[5::4]
                        for key, value in zip(keys, values):
                            try:
                                value_ = str(eval(value))
                            except:
                                value_ = value
                            condition[key] = value_
                    # Pour les conditions OR
                    else:
                        condition = []
                        conditions = ' '.join(line_elements[3:]).split(' OR ')
                        for c in conditions:
                            keys = self.extraire_node_query_elements(c)[0::4]
                            values = self.extraire_node_query_elements(c)[2::4]
                            kv = {}
                            for key, value in zip(keys, values):
                                try:
                                    value_ = str(eval(value))
                                except:
                                    value_ = value
                                kv[key] = value_
                            condition.append(kv)

                self.Condition = condition
            
            
            elif line_head == "UPDATE":
                node_name = line_elements[1][1:-1].split('{', maxsplit=1)[0].split(':', maxsplit=1)[0]
                node_property_brut = '{' + line_elements[1][1:-1].split('{', maxsplit=1)[1]
                node_id = base.get_node_by_name(node_name).Id
                original_node_property = {}
                node_property = {}
                for ele in node_property_brut[1:-1].split(', '):
                    key, value_brut = ele.split(':', maxsplit=1)
                    try:
                        original_node_property[key] = str(eval(value_brut))
                    except:
                        original_node_property[key] = value_brut
                base.update_node(node_id, "Properties", original_node_property)

                if 'WHERE' in line_elements:
                    keys = line_elements[3::4]
                    values = line_elements[5::4]
                    for key, value in zip(keys, values):
                        try:
                            value_ = str(eval(value))
                        except:
                            value_ = value
                        node_property[key] = value_

                self.Command = line_head + " Node"
                self.Id = node_id
                self.Properties = node_property

            elif line_head == "DELETE":
                node_name = line_elements[1][1:-1]
                node_id = base.get_node_by_name(node_name).Id
                self.Command = line_head + " Node"
                self.Id = node_id
        # Pour EDGE
        elif '[' in line and line_head != 'LINK':
            line_elements = self.extraire_elements(line)
            if line_head == "CREATE":
                source_node_name, target_node_name = line_elements[1].strip("[]").split(':', maxsplit=1)[0].split(', ', maxsplit=1)
                source_node_id, target_node_id = base.get_node_by_name(source_node_name).Id, base.get_node_by_name(target_node_name).Id
                edge_class = line_elements[1].strip("[]").split(':', maxsplit=1)[1].split('{', maxsplit=1)[0]
                edge_property_brut = line_elements[1].strip("[]").split(':', maxsplit=1)[1][len(edge_class):]
                edge_property = {}
                for ele in edge_property_brut[1:-1].split(', '):
                    key, value = ele.split(':', maxsplit=1)
                    try:
                        edge_property[key] = str(eval(value))
                    except:
                        edge_property[key] = value
                self.Command = line_head + " Edge"
                self.Id = (source_node_id, target_node_id)
                self.Class = edge_class
                self.Properties = edge_property

            elif line_head == "READ":
                if line_elements[1] == '[]':
                    self.Command = line_head + " Edge FIND ALL"
                elif line_elements[1][1:-1].startswith(':'):
                    self.Command = line_head + " Edge CLASS"
                    class_name = line_elements[1][1:-1].split(':', maxsplit=1)[1]
                    self.Class = class_name
                else:
                    self.Command = line_head + " Edge SPECIFIC"
                    source_name, target_name = line_elements[1][1:-1].split(', ', maxsplit=1)
                    self.Id = (base.get_node_by_name(source_name).Id, base.get_node_by_name(target_name).Id)
                condition = {}
                if 'WHERE' in line_elements:
                    if 'OR' not in line_elements[5:]:
                        keys = line_elements[3::4]
                        values = line_elements[5::4]
                        for key, value in zip(keys, values):
                            try:
                                value_ = str(eval(value))
                            except:
                                value_ = value
                            condition[key] = value_
                    else:
                        condition = []
                        conditions = ' '.join(line_elements[3:]).split(' OR ')
                        # ['Duration = Temporary', 'Years = 1000']
                        for c in conditions:
                            keys = self.extraire_node_query_elements(c)[0::4]
                            values = self.extraire_node_query_elements(c)[2::4]
                            kv = {}
                            for key, value in zip(keys, values):
                                try:
                                    value_ = str(eval(value))
                                except:
                                    value_ = value
                                kv[key] = value_
                            condition.append(kv)

                self.Condition = condition
            
            elif line_head == "UPDATE":
                source_node_name, target_node_name = line_elements[1].strip("[]").split(':', maxsplit=1)[0].split(', ', maxsplit=1)
                edge_class = line_elements[1].strip("[]").split(':', maxsplit=1)[1].split('{', maxsplit=1)[0] 
                edge_to_change = base.get_edge_by_class_and_nodes_names(edge_class, source_node_name, target_node_name).Id
                edge_property_brut = line_elements[1].strip("[]").split(':', maxsplit=1)[1][len(edge_class):]
                original_edge_property = {}
                for ele in edge_property_brut[1:-1].split(', '):
                    key, value = ele.split(':', maxsplit=1)
                    try:
                        original_edge_property[key] = str(eval(value))
                    except:
                        original_edge_property[key] = value
                base.update_edge(edge_to_change, 'Properties', original_edge_property)

                edge_property = {}
                if 'WHERE' in line_elements:
                    keys = line_elements[3::4]
                    values = line_elements[5::4]
                    for key, value in zip(keys, values):
                        try:
                            value_ = str(eval(value))
                        except:
                            value_ = value
                        edge_property[key] = value_
                self.Command = line_head + " Edge"
                self.Id = edge_to_change
                self.Properties = edge_property

            elif line_head == "DELETE":
                self.Command = line_head + " Edge"
                if not line_elements[1][1:-1].startswith(':'):
                    source_node_name, target_node_name = line_elements[1].strip("[]").split(', ', maxsplit=1)
                    edge_to_delete = base.get_edge_by_nodes_names(source_node_name, target_node_name).Id
                    self.Id = edge_to_delete
                else:
                    edges = base.get_edges_by_class(line_elements[1].strip("[]")[1:])
                    self.Id = [edge.Id for edge in edges]

        # LINK
        else:
            self.Command = "LINK"
            line_elements = self.extraire_elements(line)
            source, end = line_elements[1][1:-1].split(', ')
            source = source.strip('""')
            end = end.strip('""')
            self.Id = (base.get_node_by_name(source).Id, base.get_node_by_name(end).Id)
            if len(line_elements) > 2 and len(line_elements) <= 4:
                if line_elements[2] == "ALL":
                    self.Condition['MAX_LENGTH'] = None
                    self.Condition['MIN_LENGTH'] = None
                elif line_elements[2] == "MAX_LENGTH":
                    self.Condition['MAX_LENGTH'] = int(line_elements[-1])
                    self.Condition['MIN_LENGTH'] = None
                elif line_elements[2] == "MIN_LENGTH":
                    self.Condition['MIN_LENGTH'] = int(line_elements[-1])
                    self.Condition['MAX_LENGTH'] = None
            elif len(line_elements) == 6:
                if line_elements[2] == "MAX_LENGTH":
                    self.Condition['MAX_LENGTH'] = int(line_elements[3])
                    self.Condition['MIN_LENGTH'] = int(line_elements[5])
                elif line_elements[2] == "MIN_LENGTH":
                    self.Condition['MIN_LENGTH'] = int(line_elements[3])
                    self.Condition['MAX_LENGTH'] = int(line_elements[5])
            

class ORQueryExecutor:
    def __init__(self, query:str, base:OneRingDB, ignore_direction=False):
        self.Cleand_query:List[str] = self.clean_query(query)
        self.execute_queries(base, ignore_direction)

    def clean_query(self, query_brut)->List[str]:
        """Nettoyer la requête entière et faire une vérification des mots-clés."""
        possible_line_heads = set(['--', 'CREATE', 'READ', 'UPDATE', 'DELETE', 'LINK', 'COLOR', 'LINEARISE', 'CLUSTER'])
        only_query_lines = []
        for line in query_brut.split('\n'):
            if not line:
                pass
            else:
                line_head = line.split(' ')[0]
                if line_head not in possible_line_heads:
                    raise SyntaxError(f"{line} n'a pas une en-tête valable.")
                if line_head != '--':
                    only_query_lines.append(line)
        return only_query_lines
    
    def execute_queries(self, base, ignore_direction=False):
        """Exécuter chaque ligne itérativement"""
        for q in self.Cleand_query:
            parsed_query = ORQueryParser(q, base)
            return_object = self.execute_single_query(parsed_query, base, ignore_direction)
            st.success("✅ Requête exécutée avec succès.")
            if type(return_object) is dict:
                st.session_state.return_object = return_object
                for k, v in return_object.items():
                    st.write(k, v)

    def BFS(self, graph, source, end):
        """Chercher le plus court chemin entre deux nœuds"""
        node_status = {node:"white" for node in graph}
        node_status[source] = "gray"

        paths = {node:[] for node in graph}
        paths[source].append(source)

        queue = [source]

        while queue:
            current_node = queue.pop(0)

            for neighbour in graph[current_node]:
                if node_status[neighbour] == "white":
                    node_status[neighbour] = "gray"
                    paths[neighbour] = paths[current_node] + [neighbour]
                    queue.append(neighbour)
            node_status[current_node] = "black"
        
        return paths[end]

    def find_all_paths(self, graph, source, end, max_length=None, min_length=None):
        """Trouver tous les chemins entre deux nœuds avec option max_length et min_length"""
        paths = []
        queue = [[source]]

        while queue:
            current_path = queue.pop(0)
            current_node = current_path[-1]

            if current_node == end:
                path_length = len(current_path) - 1
                if (max_length is None or path_length <= max_length) and \
                (min_length is None or path_length >= min_length):
                    paths.append(current_path)
                continue

            if max_length is not None and len(current_path) - 1 >= max_length:
                continue

            for neighbour in graph.get(current_node, []):
                if neighbour not in current_path:
                    new_path = current_path + [neighbour]
                    queue.append(new_path)

        return paths


    def execute_single_query(self, parsed_query:ORQueryParser, base:OneRingDB, ignore_direction=False):
        """Exécuter une ligne de requête."""
        # Requête CLUSTER
        if parsed_query.Command.startswith('CLUSTER'):
            if 'NOT' in parsed_query.Command:
                st.session_state.CLUSTER = False
            else:
                st.session_state.CLUSTER = True
            return
        
        # =============== COLOR ================
        if parsed_query.Command.startswith('COLOR'):
            if 'NOT' in parsed_query.Command:
                st.session_state.COLOR = False
            else:
                st.session_state.COLOR = True
            return
        # =============== COLOR ================

        # =============== LINEARISE ================
        if parsed_query.Command.startswith('LINEARISE'):
            if 'NOT' in parsed_query.Command:
                st.session_state.LINEARISE = False
            else:
                st.session_state.LINEARISE = True
            return
        # =============== LINEARISE ================

        # Requête sur les nœuds
        if "Node" in parsed_query.Command:
            command = parsed_query.Command.split()[0]
            if command == "CREATE":
                base.create_node(parsed_query.Id, parsed_query.Class, parsed_query.Properties)
            elif command == "READ":
                if 'CLASS' in parsed_query.Command:
                    # Si on cherche pas de Hubs
                    if parsed_query.Class != 'Hubs':
                        founded_nodes = base.get_nodes_by_class(parsed_query.Class, parsed_query.Condition)
                        if parsed_query.Condition:
                            # Si les conditions sont conjointes
                            if type(parsed_query.Condition) is dict:
                                return {f"Les nœuds de la classe {parsed_query.Class} avec la condition conjointe {parsed_query.Condition} sont :" : [node.Name for node in founded_nodes]}
                            # Si les conditions sont disjointes
                            else:
                                return {f"Les nœuds de la classe {parsed_query.Class} avec la condition disjointe {parsed_query.Condition} sont :" : [node.Name for node in founded_nodes]}
                        else:
                            return {f"Les nœuds de la classe {parsed_query.Class} sont :" : [node.Name for node in founded_nodes]}
                    else:
                        # Chercher les Hubs
                        founded_nodes = base.get_nodes_by_HUB(parsed_query.Condition)
                        if not founded_nodes:
                            st.warning("Aucun nœud HUB trouvé. Il est possible que le clustering n'ait pas encore été effectué, ou que vous ayez lancé une requête de recherche de HUBs immédiatement après le clustering. Dans ce cas, veuillez relancer la requête de recherche de HUBs.")
                        else:
                            if parsed_query.Condition:
                                if type(parsed_query.Condition) is dict:
                                    return {f"Les nœuds HUB avec la condition conjointe {parsed_query.Condition} sont :" : [node.Name for node in founded_nodes]}
                                else:
                                    return {f"Les nœuds HUB avec la condition disjointe {parsed_query.Condition} sont :" : [node.Name for node in founded_nodes]}
                            else:
                                return {f"Les nœuds HUB sont :" : [node.Name for node in founded_nodes]}
                elif 'SPECIFIC' in parsed_query.Command:
                    return {f"Les informations du nœud {base.get_node_by_id(parsed_query.Id).Name} :" : str(base.get_node_by_id(parsed_query.Id))}
                elif 'ALL' in parsed_query.Command:
                    founded_nodes = base.get_all_nodes(parsed_query.Condition)
                    if parsed_query.Condition:
                        if type(parsed_query.Condition) is dict:
                            return {f"Tous les nœuds avec la condition conjointe {parsed_query.Condition} sont :" : [node.Name for node in founded_nodes]}
                        else:
                            return {f"Tous les nœuds avec la condition disjointe {parsed_query.Condition} sont :" : [node.Name for node in founded_nodes]}
                    else:
                        return {f"Tous les nœuds sont :" : [node.Name for node in founded_nodes]}
            elif command == "UPDATE":
                base.update_node(parsed_query.Id, "Properties", parsed_query.Properties)
            elif command == "DELETE":
                base.delete_node(parsed_query.Id)
        elif "Edge" in parsed_query.Command:
            command = parsed_query.Command.split()[0]
            if command == "CREATE":
                source_node_id, target_node_id = parsed_query.Id
                base.create_edge(source_node_id, target_node_id, parsed_query.Class, parsed_query.Properties)
            elif command == "READ":
                if 'FIND ALL' in parsed_query.Command:
                    all_edges = base.get_all_edges(parsed_query.Condition)
                    if parsed_query.Condition:
                        if type(parsed_query.Condition) is dict:
                            return {f"Tous les nœuds avec la condition conjointe {parsed_query.Condition} sont :" : [edge.__str__() for edge in all_edges]}
                        elif type(parsed_query.Condition) is list:
                            return {f"Tous les nœuds avec la condition disjointe {parsed_query.Condition} sont :" : [edge.__str__() for edge in all_edges]}
                    else:
                        return {f"Tous les nœuds sont :" : [edge.__str__() for edge in all_edges]}
                elif 'SPECIFIC' in parsed_query.Command:
                    source_id, target_id = parsed_query.Id
                    founded_edge = base.get_edge_by_nodes_names(base.get_node_by_id(source_id).Name, base.get_node_by_id(target_id).Name)
                    return {f"L'arête entre {base.get_node_by_id(source_id).Name} et {base.get_node_by_id(target_id).Name} est :" : founded_edge.__str__()}
                else:
                    founded_edges = base.get_edges_by_class(parsed_query.Class, parsed_query.Condition)
                    if parsed_query.Condition:
                        if type(parsed_query.Condition) is dict:
                            return {f"Les arêtes trouvées de la classe {parsed_query.Class} avec la condition conjointe {parsed_query.Condition} sont :" : [edge.__str__() for edge in founded_edges]}
                        else:
                            return {f"Les arêtes trouvées de la classe {parsed_query.Class} avec la condition disjointe {parsed_query.Condition} sont :" : [edge.__str__() for edge in founded_edges]}
                    else:
                        return {f"Les arêtes trouvées de la classe {parsed_query.Class} sont :" : [edge.__str__() for edge in founded_edges]}
            elif command == "UPDATE":
                base.update_edge(parsed_query.Id, "Properties", parsed_query.Properties)
            elif command == "DELETE":
                if type(parsed_query.Id) is not list:
                    base.delete_edge(parsed_query.Id)
                else:
                    for edge_id in parsed_query.Id:
                        base.delete_edge(edge_id)
        else:
            all_nodes = base.get_all_nodes()

            if ignore_direction:
                nodes_to_neighbours = {k.Id:list(k.Neighbours) for k in all_nodes}
            else:
                # ========= <DIRECTED GRAPH> =========
                nodes_to_neighbours = {}
                for k in all_nodes:
                    nodes_to_neighbours[k.Id] = []
                    for neighbour in list(k.Neighbours):
                        try:
                            base.get_edge_by_nodes_names(k.Name, base.get_node_by_id(neighbour).Name)
                            nodes_to_neighbours[k.Id].append(neighbour)
                        except ValueError:
                            continue
                # ========= </DIRECTED GRAPH> =========
            source, end = parsed_query.Id
            if parsed_query.Condition:
                all_paths_in_id = self.find_all_paths(nodes_to_neighbours, source, end, parsed_query.Condition['MAX_LENGTH'], parsed_query.Condition['MIN_LENGTH'])
                all_path = []
                for nodes in all_paths_in_id:
                    all_path.append([])
                    for node_id in nodes:
                        all_path[-1].append(base.get_node_by_id(node_id).Name)
                return {f"Tous les chemins entre {base.get_node_by_id(source).Name} et {base.get_node_by_id(end).Name} avec la condition {parsed_query.Condition} :" : all_path}
            else:
                return {f"Le chemin le plus court entre {base.get_node_by_id(source).Name} et {base.get_node_by_id(end).Name} :": [base.get_node_by_id(node).Name for node in self.BFS(nodes_to_neighbours, source, end)]}
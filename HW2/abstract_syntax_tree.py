from enum import Enum


class NodeType(Enum):
    Operator = 1
    Term = 2


class ASTNode:
    skip_pointers_list = []  # static

    def __init__(self, token, node_type, cost=0, child_nodes=None, result_list=None, evaluated=False):
        if child_nodes is None:
            child_nodes = list()
        if result_list is None:
            result_list = list()

        self.token = token
        self.type = node_type
        self.cost = cost
        self.result_list = result_list
        self.evaluated = evaluated
        self.child_nodes = child_nodes

        self.operation_lst = []  # used when this AST node stand for multiple AND or AND_NOT operation

    @classmethod
    def load_skip_pointers(cls, skip_pointers):
        ASTNode.skip_pointers_list = skip_pointers
        return

    def post_order_traverse(self):
        ans = list()
        if self.type == NodeType.Operator:
            ans.append("(")
            for node in self.child_nodes:
                ans.extend(node.post_order_traverse())
            if len(self.operation_lst) == 0:
                ans.append(self.token)
            else:
                ans.append(self.operation_lst)
            ans.append(")")
        else:
            ans.append("%s:%s" % (self.token, len(self.result_list)))

        return ans

    # move pointers to next possible position
    # if include_res=True, will return the postings to be included together
    @staticmethod
    def move_next(doc, lst, pos, skip_pointers, skip_idx, include_res=False):
        if include_res:
            temp_res = list()
        if skip_idx < len(skip_pointers) - 1 and pos == skip_pointers[skip_idx]:
            skip_idx = skip_idx + 1
            if lst[skip_pointers[skip_idx]] <= doc:
                if include_res:
                    for i in range(pos+1, skip_pointers[skip_idx]):
                        temp_res.append(lst[i])
                    return skip_pointers[skip_idx], skip_idx, temp_res
                else:
                    return skip_pointers[skip_idx], skip_idx

        if include_res:
            return pos+1, skip_idx, temp_res
        else:
            return pos+1, skip_idx

    def intersect(self, ls1, lst2):
        pos1, pos2 = 0, 0
        skip_idx1, skip_idx2 = 1, 1
        len1, len2 = len(ls1), len(lst2)
        skip_pointers1, skip_pointers2 = ASTNode.skip_pointers_list[len1], ASTNode.skip_pointers_list[len2]
        result = list()

        while pos1 < len1 and pos2 < len2:
            doc1, doc2 = ls1[pos1], lst2[pos2]
            if doc1 == doc2:
                result.append(doc1)
                pos1 = pos1 + 1
                pos2 = pos2 + 1
            elif doc1 < doc2:
                pos1, skip_idx1 = self.move_next(doc2, ls1, pos1, skip_pointers1, skip_idx1)
            else:
                pos2, skip_idx2 = self.move_next(doc1, lst2, pos2, skip_pointers2, skip_idx2)
        return result

    def union(self, ls1, lst2):
        pos1, pos2 = 0, 0
        skip_idx1, skip_idx2 = 0, 0
        len1, len2 = len(ls1), len(lst2)
        skip_pointers1, skip_pointers2 = ASTNode.skip_pointers_list[len1], ASTNode.skip_pointers_list[len2]
        result = list()

        while pos1 < len1 and pos2 < len2:
            doc1, doc2 = ls1[pos1], lst2[pos2]
            if doc1 == doc2:
                result.append(doc1)
                pos1 = pos1 + 1
                pos2 = pos2 + 1
            elif doc1 < doc2:
                result.append(doc1)
                pos1, skip_idx1, temp_res = \
                    self.move_next(doc2, ls1, pos1, skip_pointers1, skip_idx1, include_res=True)
                result.extend(temp_res)
            else:
                result.append(doc2)
                pos2, skip_idx2, temp_res = \
                    self.move_next(doc1, lst2, pos2, skip_pointers2, skip_idx2, include_res=True)
                result.extend(temp_res)
        result.extend(ls1[pos1:len(ls1)])
        result.extend(lst2[pos2:len(lst2)])
        return result

    def diff(self, ls1, lst2):
        pos1, pos2 = 0, 0
        skip_idx1, skip_idx2 = 0, 0
        len1, len2 = len(ls1), len(lst2)
        skip_pointers1, skip_pointers2 = ASTNode.skip_pointers_list[len1], ASTNode.skip_pointers_list[len2]
        result = list()
        while pos1 < len1 and pos2 < len2:
            doc1, doc2 = ls1[pos1], lst2[pos2]
            if doc1 == doc2:
                pos1 = pos1 + 1
                pos2 = pos2 + 1
            elif doc1 < doc2:
                result.append(doc1)
                pos1, skip_idx1, temp_res = \
                    self.move_next(doc2, ls1, pos1, skip_pointers1, skip_idx1, include_res=True)
                result.extend(temp_res)
            else:
                pos2, skip_idx2 = self.move_next(doc1, lst2, pos2, skip_pointers2, skip_idx2)
        result.extend(ls1[pos1:len(ls1)])
        return result

    def evaluate(self, all_documents_list):
        if self.evaluated:
            return

        for node in self.child_nodes:
            node.evaluate(all_documents_list)

        if len(self.operation_lst) > 0:  # for AND and AND_NOT in non-binary tree case
            self.result_list = self.child_nodes[0].result_list
            for i in range(len(self.operation_lst)):
                if self.operation_lst[i] == "AND":
                    self.result_list = list(sorted(self.intersect(self.result_list, self.child_nodes[1+i].result_list)))
                else:
                    assert self.operation_lst[i] == "AND_NOT"
                    self.result_list = list(sorted(self.diff(self.result_list, self.child_nodes[1 + i].result_list)))
            return

        # for NOT in binary tree or non-binary tree case
        if self.token == "NOT":
            self.result_list = list(sorted(self.diff(all_documents_list, self.child_nodes[0].result_list)))
            return

        # for OR in binary tree or non-binary tree case
        if self.token == "OR":
            self.result_list = self.child_nodes[0].result_list
            for node in self.child_nodes[1:]:
                self.result_list = list(sorted(self.union(self.result_list, node.result_list)))
            return

        # for AND in binary tree case
        if self.token == "AND":
            self.result_list = self.child_nodes[0].result_list
            for node in self.child_nodes[1:]:
                self.result_list = list(sorted(self.intersect(self.result_list, node.result_list)))
            return

        # for AND_NOT in binary tree case
        if self.token == "AND_NOT":
            self.result_list = self.child_nodes[0].result_list
            for node in self.child_nodes[1:]:
                self.result_list = list(sorted(self.diff(self.result_list, node.result_list)))
            return

    # can only be used when the tree is binary, flatten the binary tree into a non-binary one.
    # operation with same preference are merged into one big node.
    # AND and AND_NOT have same preference if they are indeed parallel.
    # i.e. for `a AND b AND NOT c AND d`, `a, b, c, d` are parallel
    # but for `a AND b AND NOT (c AND d)`, `a, b, (c AND d) are parallel`
    def flatten(self, all_documents_list):
        if self.type == NodeType.Term:
            return
        for node in self.child_nodes:
            node.flatten(all_documents_list)

        if self.token == "NOT":  # can not optimize as NOT NOT already handled by string replacement
            self.cost = len(all_documents_list) + self.child_nodes[0].cost
            return

        flatten_child_nodes = list()
        if self.token == "OR":
            for node in self.child_nodes:
                if node.token == "OR":
                    flatten_child_nodes.extend(node.child_nodes)
                else:
                    flatten_child_nodes.append(node)

        # for AND, AND or AND_NOT in both child can be merged
        if self.token == "AND":
            left_node = self.child_nodes[0]
            right_node = self.child_nodes[1]
            if left_node.token == "AND" or left_node.token == "AND_NOT":
                self.operation_lst.extend(left_node.operation_lst)
                flatten_child_nodes.extend(left_node.child_nodes)
            else:
                flatten_child_nodes.append(left_node)

            self.operation_lst.append("AND")

            if right_node.token == "AND" or right_node.token == "AND_NOT":
                self.operation_lst.extend(right_node.operation_lst)

                flatten_child_nodes.extend(right_node.child_nodes)
            else:
                flatten_child_nodes.append(right_node)

        # for AND_NOT, only AND or AND_NOT in left child can be merged
        if self.token == "AND_NOT":
            left_node = self.child_nodes[0]
            right_node = self.child_nodes[1]
            if left_node.token == "AND" or left_node.token == "AND_NOT":
                self.operation_lst.extend(left_node.operation_lst)
                flatten_child_nodes.extend(left_node.child_nodes)
            else:
                flatten_child_nodes.append(left_node)

            self.operation_lst.append("AND_NOT")
            flatten_child_nodes.append(right_node)

        self.child_nodes = flatten_child_nodes
        self.cost = sum([node.cost for node in self.child_nodes])

        # code bellow are sorting the child nodes based on its cost.
        # for OR, it is sort from low to high by its cost
        # for AND/AND_NOT, it is sorted in the form of `start_term [AND NOT term]+ [AND term]+`
        # and each term are sorted from low to high. start_term is the lowest cost term in `AND term`s
        if len(self.operation_lst) > 0:
            and_nodes = [self.child_nodes[0]]
            and_not_nodes = []
            for i in range(len(self.operation_lst)):
                if self.operation_lst[i] == "AND":
                    and_nodes.append(self.child_nodes[1 + i])
                else:
                    and_not_nodes.append(self.child_nodes[1 + i])

            and_nodes = list(sorted(and_nodes, key=lambda x: x.cost))
            and_not_nodes = list(sorted(and_not_nodes, key=lambda x: x.cost))
            final_child_nodes_list = list()
            final_operation_list = list()
            final_child_nodes_list.append(and_nodes[0])
            for node in and_not_nodes:
                final_child_nodes_list.append(node)
                final_operation_list.append("AND_NOT")
            for node in and_nodes[1:]:
                final_child_nodes_list.append(node)
                final_operation_list.append("AND")
            self.child_nodes = final_child_nodes_list
            self.operation_lst = final_operation_list
        else:
            self.child_nodes = list(sorted(self.child_nodes, key=lambda x: x.cost))


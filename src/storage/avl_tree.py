# ======================= AVL TREE MODULE =======================
# This file defines a manual AVL Tree data structure used for indexing.
# Steps:
# 1. Create Node class (key, value, height, left, right)
# 2. Implement insert(), delete(), search() functions
# 3. Add rotations (LL, RR, LR, RL) to keep balance
# 4. Include in_order() traversal for debugging and range queries
# Purpose: Ensure O(log n) performance for data lookups and updates.

class AVLNode:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.height = 1
        self.left = None
        self.right = None


class AVLTree:

    def insert(self, root, key, value):
        if not root:
            return AVLNode(key, value)
        elif key < root.key:
            root.left = self.insert(root.left, key, value)
        else:
            root.right = self.insert(root.right, key, value)

        # FIXED: removed extra parenthesis
        root.height = 1 + max(self.get_height(root.left), self.get_height(root.right))
        balance = self.get_balance(root)

        # Left Left
        if balance > 1 and key < root.left.key:
            return self.right_rotate(root)

        # Right Right
        if balance < -1 and key > root.right.key:
            return self.left_rotate(root)

        # Left Right
        if balance > 1 and key > root.left.key:
            root.left = self.left_rotate(root.left)
            return self.right_rotate(root)

        # Right Left
        if balance < -1 and key < root.right.key:
            root.right = self.right_rotate(root.right)
            return self.left_rotate(root)

        return root


    def delete(self, root, key):
        if not root:
            return root

        elif key < root.key:
            root.left = self.delete(root.left, key)

        elif key > root.key:
            root.right = self.delete(root.right, key)

        else:
            if not root.left:
                return root.right
            elif not root.right:
                return root.left

            temp = self.get_min_value_node(root.right)
            root.key = temp.key
            root.value = temp.value
            root.right = self.delete(root.right, temp.key)

        if not root:
            return root

        # FIXED
        root.height = 1 + max(self.get_height(root.left), self.get_height(root.right))
        balance = self.get_balance(root)

        # Left Left
        if balance > 1 and self.get_balance(root.left) >= 0:
            return self.right_rotate(root)

        # Left Right
        if balance > 1 and self.get_balance(root.left) < 0:
            root.left = self.left_rotate(root.left)
            return self.right_rotate(root)

        # Right Right
        if balance < -1 and self.get_balance(root.right) <= 0:
            return self.left_rotate(root)

        # Right Left
        if balance < -1 and self.get_balance(root.right) > 0:
            root.right = self.right_rotate(root.right)
            return self.left_rotate(root)

        return root


    def search(self, root, key):
        if not root or root.key == key:
            return root
        if key < root.key:
            return self.search(root.left, key)
        return self.search(root.right, key)


    def left_rotate(self, z):
        y = z.right
        T2 = y.left

        y.left = z
        z.right = T2

        z.height = 1 + max(self.get_height(z.left), self.get_height(z.right))
        y.height = 1 + max(self.get_height(y.left), self.get_height(y.right))

        return y


    def right_rotate(self, z):
        y = z.left
        T3 = y.right

        y.right = z
        z.left = T3

        z.height = 1 + max(self.get_height(z.left), self.get_height(z.right))
        y.height = 1 + max(self.get_height(y.left), self.get_height(y.right))

        return y


    def get_height(self, root):
        return root.height if root else 0


    def get_balance(self, root):
        if not root:
            return 0
        return self.get_height(root.left) - self.get_height(root.right)


    def get_min_value_node(self, root):
        while root.left:
            root = root.left
        return root


    def in_order(self, root):
        res = []
        if root:
            res = self.in_order(root.left)
            res.append((root.key, root.value))
            res += self.in_order(root.right)
        return res

# ======================= END OF AVL TREE MODULE =======================

# # Example usage:
# avl = AVLTree()   
# root = None
# keys_values = [(10, 'A'), (20, 'B'), (30, 'C'), (40, 'D'), (50, 'E'), (25, 'F')]
# for key, value in keys_values:
#     root = avl.insert(root, key, value)     
#     print("In-order traversal after inserts:", avl.in_order(root))
# root = avl.delete(root, 20)
# print("In-order traversal after deletion of 20:", avl.in_order(root))
# # Search for a key
# result = avl.search(root, 25)
# if result:
#     print(f"Found key 25 with value: {result.value}")

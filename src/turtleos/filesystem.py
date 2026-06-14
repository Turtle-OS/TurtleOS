"""
Sistema de arquivos virtual do TurtleOS.

Tudo fica guardado em memoria (e pode ser salvo em um arquivo .json
para persistir entre sessoes). Cada "diretorio" e um dict com:
    {"type": "dir", "children": {nome: node, ...}}
Cada "arquivo" e um dict com:
    {"type": "file", "content": "texto..."}
"""

import json
import os
import time


class VFSError(Exception):
    pass


class VirtualFileSystem:
    def __init__(self, save_path=None):
        self.save_path = save_path
        self.root = {"type": "dir", "children": {}}
        self.cwd = ["home", "tartaruga"]

        if save_path and os.path.exists(save_path):
            try:
                self.load()
                return
            except Exception:
                pass

        self._seed()

    # ------------------------------------------------------------ seed
    def _seed(self):
        readme = (
            "Bem-vindo ao TurtleOS!\n\n"
            "Este e um sistema de arquivos virtual: tudo o que voce criar\n"
            "aqui (pastas, arquivos) existe apenas dentro do simulador.\n\n"
            "Digite 'help' no terminal para ver os comandos disponiveis.\n"
        )
        self.root["children"] = {
            "home": {
                "type": "dir",
                "children": {
                    "tartaruga": {
                        "type": "dir",
                        "children": {
                            "leiame.txt": {"type": "file", "content": readme},
                            "documentos": {"type": "dir", "children": {}},
                            "imagens": {"type": "dir", "children": {}},
                        },
                    }
                },
            },
            "sistema": {
                "type": "dir",
                "children": {
                    "versao.txt": {"type": "file", "content": "TurtleOS v1.0\n"},
                },
            },
        }

    # ------------------------------------------------------------ path helpers
    def _split(self, path):
        return [p for p in path.replace("\\", "/").split("/") if p not in ("", ".")]

    def _resolve(self, path):
        """Retorna a lista de componentes (a partir da raiz) para `path`."""
        if path is None or path == "":
            parts = list(self.cwd)
        elif path.startswith("/"):
            parts = self._split(path)
        else:
            parts = list(self.cwd) + self._split(path)

        result = []
        for part in parts:
            if part == "..":
                if result:
                    result.pop()
            else:
                result.append(part)
        return result

    def _get_node(self, parts):
        node = self.root
        for part in parts:
            if node["type"] != "dir" or part not in node["children"]:
                return None
            node = node["children"][part]
        return node

    def _get_parent_and_name(self, path):
        parts = self._resolve(path)
        if not parts:
            raise VFSError("caminho invalido")
        parent = self._get_node(parts[:-1])
        if parent is None or parent["type"] != "dir":
            raise VFSError("diretorio nao encontrado")
        return parent, parts[-1], parts

    # ------------------------------------------------------------ public api
    def pwd(self):
        return "/" + "/".join(self.cwd)

    def cd(self, path):
        parts = self._resolve(path)
        node = self._get_node(parts)
        if node is None:
            raise VFSError(f"diretorio nao encontrado: {path}")
        if node["type"] != "dir":
            raise VFSError(f"nao e um diretorio: {path}")
        self.cwd = parts

    def ls(self, path=None):
        parts = self._resolve(path)
        node = self._get_node(parts)
        if node is None:
            raise VFSError(f"caminho nao encontrado: {path}")
        if node["type"] == "file":
            return [os.path.basename("/" + "/".join(parts))]
        entries = []
        for name, child in sorted(node["children"].items()):
            entries.append(name + ("/" if child["type"] == "dir" else ""))
        return entries

    def mkdir(self, path):
        parent, name, parts = self._get_parent_and_name(path)
        if name in parent["children"]:
            raise VFSError(f"ja existe: {name}")
        parent["children"][name] = {"type": "dir", "children": {}}

    def touch(self, path):
        parent, name, parts = self._get_parent_and_name(path)
        if name not in parent["children"]:
            parent["children"][name] = {"type": "file", "content": ""}

    def rm(self, path, recursive=False):
        parent, name, parts = self._get_parent_and_name(path)
        if name not in parent["children"]:
            raise VFSError(f"nao encontrado: {path}")
        node = parent["children"][name]
        if node["type"] == "dir" and node["children"] and not recursive:
            raise VFSError(f"diretorio nao vazio: {path} (use 'rm -r')")
        del parent["children"][name]

    def read(self, path):
        parts = self._resolve(path)
        node = self._get_node(parts)
        if node is None:
            raise VFSError(f"nao encontrado: {path}")
        if node["type"] != "file":
            raise VFSError(f"e um diretorio: {path}")
        return node["content"]

    def write(self, path, content, append=False):
        parts = self._resolve(path)
        node = self._get_node(parts)
        if node is not None and node["type"] == "dir":
            raise VFSError(f"e um diretorio: {path}")
        if node is None:
            parent, name, _ = self._get_parent_and_name(path)
            node = {"type": "file", "content": ""}
            parent["children"][name] = node
        if append:
            node["content"] += content
        else:
            node["content"] = content

    def exists(self, path):
        return self._get_node(self._resolve(path)) is not None

    def is_dir(self, path):
        node = self._get_node(self._resolve(path))
        return node is not None and node["type"] == "dir"

    def tree(self, path=None, prefix=""):
        parts = self._resolve(path)
        node = self._get_node(parts)
        if node is None:
            raise VFSError(f"nao encontrado: {path}")
        lines = []

        def walk(n, pre):
            if n["type"] != "dir":
                return
            children = sorted(n["children"].items())
            for i, (name, child) in enumerate(children):
                last = i == len(children) - 1
                branch = "+-- " if last else "|-- "
                lines.append(pre + branch + name + ("/" if child["type"] == "dir" else ""))
                if child["type"] == "dir":
                    walk(child, pre + ("    " if last else "|   "))

        walk(node, "")
        return lines

    # ------------------------------------------------------------ persistence
    def save(self, path=None):
        path = path or self.save_path
        if not path:
            return
        data = {"root": self.root, "cwd": self.cwd, "saved_at": time.time()}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def load(self, path=None):
        path = path or self.save_path
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.root = data["root"]
        self.cwd = data.get("cwd", ["home", "tartaruga"])

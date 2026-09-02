"""Cliente para o MCP HTTP da Nekt.

A Nekt expõe o warehouse (Athena) pela ferramenta `execute_sql` do seu MCP server.
Não há endpoint REST de query na API v1 — `/api/v1/queries/` só guarda o SQL, não o
executa —, por isso o painel fala com o MCP.

Autenticação: `NEKT_MCP_TOKEN` (Bearer). Endpoint em `NEKT_MCP_URL`.
"""

from __future__ import annotations

import json
import os
import uuid

import pandas as pd
import requests

DEFAULT_URL = "https://mcp.locates.com.br/mcp"
TIMEOUT_S = 300


class NektError(RuntimeError):
    """Falha vinda do MCP ou do engine de query."""


class NektClient:
    """Sessão MCP mantida viva entre queries (o handshake custa um round-trip)."""

    def __init__(self, url: str | None = None, token: str | None = None):
        self.url = url or os.getenv("NEKT_MCP_URL", DEFAULT_URL)
        self.token = token or os.getenv("NEKT_MCP_TOKEN")
        if not self.token:
            raise NektError(
                "NEKT_MCP_TOKEN não definido. Exporte o token antes de subir o app "
                "(ex.: `source ~/.config/locates/secrets.env`)."
            )
        self._session = requests.Session()
        self._mcp_session_id: str | None = None
        self._connected = False

    # ── transporte ────────────────────────────────────────────────────────────
    def _rpc(self, method: str, params: dict | None = None, notify: bool = False):
        body: dict = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            body["params"] = params
        if not notify:
            body["id"] = str(uuid.uuid4())

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self._mcp_session_id:
            headers["Mcp-Session-Id"] = self._mcp_session_id

        resp = self._session.post(self.url, headers=headers, json=body, timeout=TIMEOUT_S)
        if resp.headers.get("Mcp-Session-Id"):
            self._mcp_session_id = resp.headers["Mcp-Session-Id"]
        if notify:
            return None
        if resp.status_code >= 400:
            raise NektError(f"MCP HTTP {resp.status_code}: {resp.text[:300]}")

        # O servidor responde ora JSON puro, ora SSE (`data: {...}`).
        for line in resp.text.splitlines():
            if line.startswith("data: "):
                return json.loads(line[6:])
        return resp.json()

    def connect(self) -> "NektClient":
        if self._connected:
            return self
        self._rpc(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "painel-custos-aws", "version": "1.0"},
            },
        )
        self._rpc("notifications/initialized", {}, notify=True)
        self._connected = True
        return self

    def _call_tool(self, name: str, arguments: dict) -> dict:
        self.connect()
        res = self._rpc("tools/call", {"name": name, "arguments": arguments})
        if "error" in res:
            raise NektError(f"MCP {name}: {res['error']}")
        texts = [
            item["text"]
            for item in res.get("result", {}).get("content", [])
            if item.get("type") == "text"
        ]
        if not texts:
            raise NektError(f"MCP {name}: resposta sem conteúdo textual.")
        return json.loads(texts[0])

    # ── consulta ──────────────────────────────────────────────────────────────
    def query(self, sql: str) -> pd.DataFrame:
        """Roda SQL no Athena da Nekt e devolve um DataFrame (segue a paginação)."""
        rows: list[list] = []
        columns: list[str] | None = None
        args: dict = {"sql_query": sql}

        while True:
            payload = self._call_tool("execute_sql", args)
            if payload.get("status") != "succeeded":
                raise NektError(
                    payload.get("error")
                    or payload.get("engine_error")
                    or json.dumps(payload)[:400]
                )
            columns = columns or payload.get("columns", [])
            rows.extend(payload.get("data", []))
            token = payload.get("next_page_token") or payload.get("page_token")
            if not token:
                break
            args = {"sql_query": sql, "page_token": token}

        return pd.DataFrame(rows, columns=columns or [])

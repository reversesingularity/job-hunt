"""MCP server exposing JobHunt pipeline tools."""

from __future__ import annotations

import asyncio
import json

from dotenv import load_dotenv

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from services.db import get_job, init_db, list_shortlist
from services.orchestrator.pipeline import tailor_job
from services.tailoring.fact_bank import (
    FactBankError,
    fact_bank_summary,
    load_fact_bank,
    normalize_to_internal,
)
from services.tailoring.llm import draft_cover_letter

load_dotenv()
server = Server("jobhunt")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_applicant_context",
            description="Return fact-bank summary and skill levels from master_cv.json",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="list_shortlist",
            description="Top-N scored jobs with explainable fit reasons",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 20},
                    "min_score": {"type": "number"},
                    "location": {
                        "type": "string",
                        "description": "Region filter, e.g. au,nz",
                    },
                },
            },
        ),
        Tool(
            name="tailor_for_job",
            description="Run honest tailoring pipeline for a job_id",
            inputSchema={
                "type": "object",
                "properties": {"job_id": {"type": "integer"}},
                "required": ["job_id"],
            },
        ),
        Tool(
            name="draft_cover_letter",
            description="Draft honest cover letter for a job_id using fact bank only",
            inputSchema={
                "type": "object",
                "properties": {"job_id": {"type": "integer"}},
                "required": ["job_id"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    init_db()
    if name == "get_applicant_context":
        try:
            cv = load_fact_bank()
            summary = fact_bank_summary(cv)
            return [TextContent(type="text", text=json.dumps(summary, indent=2))]
        except FactBankError as e:
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

    if name == "list_shortlist":
        limit = arguments.get("limit", 20)
        min_score = arguments.get("min_score")
        location_codes = None
        if arguments.get("location"):
            from services.scoring.location_filter import parse_location_filter
            location_codes = parse_location_filter(arguments["location"])
        jobs = list_shortlist(limit=limit, min_score=min_score, location_codes=location_codes)
        return [TextContent(type="text", text=json.dumps(jobs, indent=2))]

    if name == "tailor_for_job":
        job_id = arguments["job_id"]
        result = tailor_job(job_id)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    if name == "draft_cover_letter":
        job_id = arguments["job_id"]
        job = get_job(job_id)
        if not job:
            return [TextContent(type="text", text=json.dumps({"error": "job not found"}))]
        raw = load_fact_bank()
        cv = normalize_to_internal(raw)
        letter = draft_cover_letter(cv, job, [])
        return [TextContent(type="text", text=letter)]

    return [TextContent(type="text", text=json.dumps({"error": f"unknown tool: {name}"}))]


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())

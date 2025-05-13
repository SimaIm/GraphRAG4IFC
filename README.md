# Natural Language Question Answering over IFC Building Models using LLMs and Graph-RAG
This project demonstrates how to use Large Language Models (LLMs) with Graph Retrieval-Augmented Generation to parse and query Industry Foundation Classes (IFC) files. It allows users to ask plain-language questions about BIM data and get accurate answers powered by GPT-4o and a Neo4j graph database.

This repository is part of our paper accepted at **EC³ 2025 (European Conference on Computing in Construction)**.  
🔗 [Read the paper on arXiv](https://arxiv.org/abs/2504.16813)

---

## Project Overview

The system has two main stages:

1. **Graph Generation** – Converts an IFC file into a graph format using IFCOpenShell and stores it in Neo4j.
2. **LLM-based QA System** – Uses GPT-4o with prompt engineering to answer questions about the IFC model using Cypher queries.
3. **Main Script** – Coordinates the full pipeline from parsing to user interaction.




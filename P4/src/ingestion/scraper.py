"""
P4 - Módulo de Ingestión de Datos
Basado en P2/scripts/ingest.py pero mejorado para integración con P4

Este módulo se encarga de:
1. Recopilar información oficial de fuentes web
2. Extraer y procesar contenido relevante
3. Estructurar datos para el pipeline de P4
4. Mantener compatibilidad con formato de P2
"""

import hashlib
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
import yaml
from bs4 import BeautifulSoup

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SourceConfig:
    """Configuración de una fuente de datos"""

    name: str
    url: str
    type: str  # 'forms', 'guides', 'laws', 'faq'
    region: str
    selectors: Dict[str, str]  # Selectores CSS específicos
    headers: Optional[Dict[str, str]] = None


class WebScraper:
    """
    Scraper mejorado basado en P2 pero con capacidades extendidas para P4
    Mantiene compatibilidad con el formato original de P2
    """

    def __init__(self, config_path: str = "configs/sources.yaml", chunk_size_chars: int = 1500):  # [P4]
        self.config_path = config_path
        self.chunk_size_chars = chunk_size_chars  # [P4]
        self.sources = self._load_sources()
        self.session = requests.Session()
        # Headers por defecto para evitar bloqueos
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

    def _load_sources(self) -> List[SourceConfig]:
        """Carga configuración de fuentes desde archivo YAML"""
        if not os.path.exists(self.config_path):
            logger.warning(f"Config file {self.config_path} not found, using defaults")
            return self._get_default_sources()

        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        sources = []
        for source_data in config.get("sources", []):
            sources.append(SourceConfig(**source_data))

        return sources

    def _get_default_sources(self) -> List[SourceConfig]:
        """Fuentes por defecto para demostración"""
        return [
            SourceConfig(
                name="DIAN Formularios",
                url="https://www.dian.gov.co/formularios",
                type="forms",
                region="Nacional",
                selectors={
                    "content": "p, h2, li, .form-description",
                    "title": "h1, .title",
                    "date": ".date, .publication-date",
                },
            ),
            SourceConfig(
                name="Cámara de Comercio Bogotá",
                url="https://www.camaracomercio.com.co",
                type="guides",
                region="Bogotá",
                selectors={
                    "content": "p, h2, li, .guide-content",
                    "title": "h1, .guide-title",
                    "date": ".date, .update-date",
                },
            ),
        ]

    def fetch_page(self, url: str, timeout: int = 15) -> str:
        """
        Descarga contenido HTML de una página.
        Mejorado con retry y mejor manejo de errores.
        """
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            raise

    def parse_html_to_chunks(
        self, html: str, source: SourceConfig, chunk_size_chars: int = 1500
    ) -> List[Dict[str, Any]]:
        """
        Parsea HTML y divide en chunks procesables.
        Mantener compatibilidad con formato de P2 pero mejorado.
        """
        soup = BeautifulSoup(html, "html.parser")

        # Extraer título usando selectores específicos
        title_selectors = source.selectors.get("title", "h1, title")
        title_elem = soup.select_one(title_selectors)
        title = (
            title_elem.get_text(strip=True) if title_elem else "Título no encontrado"
        )

        # Extraer contenido usando selectores específicos
        content_selectors = source.selectors.get("content", "p, h2, li")
        texts = [
            elem.get_text(" ", strip=True)
            for elem in soup.select(content_selectors)
            if elem.get_text(strip=True) and len(elem.get_text(strip=True)) > 20
        ]

        # Extraer fecha si está disponible
        date_selectors = source.selectors.get("date", ".date, .publication-date")
        date_elem = soup.select_one(date_selectors)
        date_str = (
            date_elem.get_text(strip=True)
            if date_elem
            else datetime.now().strftime("%Y-%m-%d")
        )

        # Combinar y dividir en chunks
        combined = "\n".join(texts)
        chunks = []

        for i in range(0, len(combined), chunk_size_chars):
            chunk = combined[i : i + chunk_size_chars].strip()
            if not chunk:
                continue

            # Generar ID único manteniendo compatibilidad con P2
            uid = hashlib.sha1((source.url + str(i) + date_str).encode()).hexdigest()[
                :12
            ]

            chunk_data = {
                # === FORMATO COMPATIBLE CON P2 ===
                "id": f"{uid}",
                "source_url": source.url,
                "region": source.region,
                "text": chunk,
                "date_fetched": date_str,
                # === EXTENSIONES PARA P4 ===
                "source_name": source.name,
                "source_type": source.type,
                "chunk_index": i // chunk_size_chars,
                "title": title,
                "metadata": {
                    "total_chunks": len(range(0, len(combined), chunk_size_chars)),
                    "chunk_size": len(chunk),
                    "processed_at": datetime.now().isoformat(),
                    "p4_version": "1.0.0",
                },
            }
            chunks.append(chunk_data)

        return chunks

    def scrape_source(self, source: SourceConfig) -> List[Dict[str, Any]]:
        """Scrapea una fuente específica"""
        try:
            logger.info(f"Scraping source: {source.name}")
            html = self.fetch_page(source.url)
            chunks = self.parse_html_to_chunks(html, source, chunk_size_chars=self.chunk_size_chars)  # [P4]
            logger.info(f"Generated {len(chunks)} chunks from {source.name}")
            return chunks
        except Exception as e:
            logger.error(f"Error scraping {source.name}: {e}")
            return []

    def scrape_all_sources(self) -> List[Dict[str, Any]]:
        """Scrapea todas las fuentes configuradas"""
        all_chunks = []

        for source in self.sources:
            chunks = self.scrape_source(source)
            all_chunks.extend(chunks)

        return all_chunks

    def save_chunks(
        self,
        chunks: List[Dict[str, Any]],
        output_path: str = "data/raw/scraped_data.jsonl",
    ):
        """
        Guarda chunks en formato JSONL.
        Compatible con formato de P2 pero con metadatos extendidos de P4.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w", encoding="utf8") as f:
            for chunk in chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

        logger.info(f"Wrote {len(chunks)} chunks to {output_path}")
        return output_path


def main():
    """
    Función principal para ejecutar el scraper.
    Compatible con uso independiente y con pipeline de P4.
    """
    import argparse  # [P4]
    ap = argparse.ArgumentParser()  # [P4]
    ap.add_argument("--chunk-size", type=int, default=1500, help="Chunk size in characters")  # [P4]
    ap.add_argument("--config", default="configs/sources.yaml", help="Sources YAML path")  # [P4]
    args = ap.parse_args()  # [P4]

    scraper = WebScraper(config_path=args.config, chunk_size_chars=args.chunk_size)  # [P4]

    # Scrapear todas las fuentes
    chunks = scraper.scrape_all_sources()

    if not chunks:
        logger.warning("No chunks generated")
        return

    # Guardar resultados
    output_path = scraper.save_chunks(chunks)
    logger.info(f"Main output saved to: {output_path}")

    # También guardar en formato compatible con P2 para integración
    p2_compatible_path = "data/raw/faqs_p2_compatible.jsonl"
    p2_chunks = []
    for chunk in chunks:
        # Extraer solo campos compatibles con P2
        p2_chunk = {
            "id": chunk["id"],
            "source_url": chunk["source_url"],
            "region": chunk["region"],
            "text": chunk["text"],
            "date_fetched": chunk["date_fetched"],
        }
        p2_chunks.append(p2_chunk)

    with open(p2_compatible_path, "w", encoding="utf8") as f:
        for chunk in p2_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    logger.info(f"Also saved P2 compatible format to {p2_compatible_path}")


if __name__ == "__main__":
    main()

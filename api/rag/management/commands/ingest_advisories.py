"""Ingest the fraud-advisory RAG corpus.

Always loads the bundled seed advisories. If ``FIRECRAWL_API_KEY`` is set and
--url values are given, also crawls those live pages into the same corpus.
Idempotent: clears the corpus first unless --append is passed.
"""
from django.core.management.base import BaseCommand

from rag.corpus import SEED_ADVISORIES
from rag.ingest import ingest_document, ingest_url
from rag.models import AdvisoryChunk, AdvisorySource


class Command(BaseCommand):
    help = "Ingest fraud advisories (bundled seed + optional Firecrawl URLs)."

    def add_arguments(self, parser):
        parser.add_argument("--url", action="append", default=[],
                            help="Live advisory URL to crawl via Firecrawl (repeatable).")
        parser.add_argument("--append", action="store_true",
                            help="Keep existing corpus instead of clearing it.")

    def handle(self, *args, **opts):
        if not opts["append"]:
            AdvisoryChunk.objects.all().delete()
            AdvisorySource.objects.all().delete()

        n = 0
        for doc in SEED_ADVISORIES:
            ingest_document(**doc)
            n += 1
        self.stdout.write(self.style.SUCCESS(f"Ingested {n} bundled advisories."))

        crawled = 0
        for url in opts["url"]:
            src = ingest_url(url)
            if src:
                crawled += 1
                self.stdout.write(f"  crawled {url}")
            else:
                self.stdout.write(self.style.WARNING(f"  skipped {url} (no Firecrawl key / fetch failed)"))
        if opts["url"]:
            self.stdout.write(self.style.SUCCESS(f"Crawled {crawled}/{len(opts['url'])} live URLs."))

        total = AdvisoryChunk.objects.count()
        self.stdout.write(self.style.SUCCESS(f"Corpus ready: {total} chunks."))

"""
Performance test command for bulk custom field operations.

Usage:
    python manage.py test_bulk_custom_fields
    python manage.py test_bulk_custom_fields --docs 100  # Test with 100 documents
    python manage.py test_bulk_custom_fields --start 1 --end 100  # Custom range
"""

import time
from datetime import datetime

from django.core.management.base import BaseCommand

from documents.bulk_edit import modify_custom_fields
from documents.models import CustomField
from documents.models import Document


class Command(BaseCommand):
    help = "Performance test for bulk custom field operations"

    def add_arguments(self, parser):
        parser.add_argument(
            "--docs",
            type=int,
            default=50,
            help="Number of documents to test (starting from ID 1)",
        )
        parser.add_argument(
            "--start",
            type=int,
            default=1,
            help="Starting document ID",
        )
        parser.add_argument(
            "--end",
            type=int,
            default=None,
            help="Ending document ID (overrides --docs)",
        )
        parser.add_argument(
            "--custom-field-name",
            type=str,
            default="BulkTestField",
            help="Name for the custom field",
        )

    def handle(self, *args, **options):
        # Determine document ID range
        start_id = options["start"]
        end_id = options["end"] if options["end"] else start_id + options["docs"] - 1

        doc_ids = list(range(start_id, end_id + 1))

        # Configuration
        field_name = options["custom_field_name"]
        field_type = CustomField.FieldDataType.STRING

        self.stdout.write("=" * 70)
        self.stdout.write(
            self.style.SUCCESS("BULK CUSTOM FIELDS PERFORMANCE TEST"),
        )
        self.stdout.write("=" * 70)

        # Step 1: Get or create test custom field
        self.stdout.write(f"\n1. Setting up test custom field '{field_name}'...")
        test_field, created = CustomField.objects.get_or_create(
            name=field_name,
            defaults={"data_type": field_type},
        )
        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"   ✓ Created new custom field (ID: {test_field.id})",
                ),
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"   ✓ Using existing custom field (ID: {test_field.id})",
                ),
            )

        # Step 2: Check which documents exist
        self.stdout.write(
            f"\n2. Checking which documents exist in range {doc_ids[0]}-{doc_ids[-1]}...",
        )
        existing_docs = list(
            Document.objects.filter(id__in=doc_ids).values_list("id", flat=True),
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"   ✓ Found {len(existing_docs)} existing documents",
            ),
        )

        if not existing_docs:
            self.stdout.write(
                self.style.WARNING(
                    "\n   ⚠ No documents found! Please create some documents first.",
                ),
            )
            self.stdout.write("   Exiting without running performance test.")
            return

        # Step 3: Run the bulk operation with timing
        test_value = f"test_value_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.stdout.write("\n3. Running bulk custom field modification...")
        self.stdout.write(
            f"   Setting field '{field_name}' = '{test_value}' on {len(existing_docs)} documents",
        )

        start_time = time.time()

        result = modify_custom_fields(
            doc_ids=existing_docs,
            add_custom_fields={test_field.id: test_value},
            remove_custom_fields=[],
        )

        end_time = time.time()
        elapsed_time = end_time - start_time

        # Step 4: Report results
        self.stdout.write("\n4. Results:")
        self.stdout.write(
            self.style.SUCCESS(f"   Status: {result}"),
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"   Time elapsed: {elapsed_time:.4f} seconds",
            ),
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"   Documents processed: {len(existing_docs)}",
            ),
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"   Operations per second: {len(existing_docs) / elapsed_time:.2f}",
            ),
        )

        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("TEST COMPLETE"))
        self.stdout.write("=" * 70)

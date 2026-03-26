from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.expedientes.models import EventLog

class Command(BaseCommand):
    help = 'Processes pending events from the EventLog outbox queue'

    def handle(self, *args, **options):
        # Fetch up to 100 unprocessed events
        pending_events = EventLog.objects.filter(processed_at__isnull=True).order_by('occurred_at')[:100]
        
        if not pending_events:
            self.stdout.write(self.style.SUCCESS("No pending events to process."))
            return

        count = 0
        for event in pending_events:
            self.stdout.write(f"Processing Event: {event.event_id} - {event.event_type} (Aggregate: {event.aggregate_id})")
            # In Sprint 2, we just mark it as processed
            event.processed_at = timezone.now()
            event.save(update_fields=['processed_at'])
            count += 1
            
        self.stdout.write(self.style.SUCCESS(f"Successfully processed {count} events."))

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from request.models import RequirementUpload, RequestStatusHistory, PaymentUpload
from accounts.models import Request as DocRequest, RequestWorkflow, Notification


class Command(BaseCommand):
    help = 'Persist status changes for requests that have RequirementUpload rows but remain in requirement-needed statuses.'

    def add_arguments(self, parser):
        parser.add_argument('--request', dest='request_id', type=int, help='Limit to a specific request id')

    def handle(self, *args, **options):
        request_id = options.get('request_id')

        # Determine target statuses that mean the request is waiting for requirements
        requirement_statuses = RequestWorkflow.requirements_upload_statuses()

        qs = DocRequest.objects.filter(status__in=requirement_statuses)
        if request_id:
            qs = qs.filter(id=request_id)

        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.NOTICE('No requests found in requirement-waiting statuses.'))
            return

        updated = 0
        for req in qs.select_related('student'):
            # If there are any RequirementUpload rows for this request, mark as submitted
            has_req_uploads = RequirementUpload.objects.filter(request=req).exists()
            has_pay_uploads = PaymentUpload.objects.filter(request=req).exists()

            # If neither upload type exists, skip
            if not (has_req_uploads or has_pay_uploads):
                self.stdout.write(self.style.NOTICE(f'Skipping Request {req.id}: no upload rows found.'))
                continue

            previous = req.status

            # If payment uploads exist and request is waiting for payment, mark payment submitted
            if has_pay_uploads and req.status in RequestWorkflow.payment_upload_statuses():
                req.status = RequestWorkflow.PAYMENT_SUBMITTED
                if not req.payment_submitted_at:
                    req.payment_submitted_at = timezone.now()
                if not req.payment_feedback:
                    req.payment_feedback = 'Payment receipt imported from storage.'
                req.save(update_fields=['status', 'payment_submitted_at', 'payment_feedback'])

                RequestStatusHistory.objects.create(
                    request=req,
                    old_status=previous,
                    new_status=req.status,
                    changed_by='system',
                    notes='Automated: marked payment submitted because PaymentUpload records exist.'
                )

                try:
                    Notification.objects.create(
                        student=req.student,
                        request=req,
                        message=f"Payment receipt for request #{req.id} was recorded and marked as submitted."
                    )
                except Exception:
                    pass

                updated += 1
                self.stdout.write(self.style.SUCCESS(f'Updated Request {req.id}: {previous} -> {req.status}'))
                continue

            # Otherwise, mark requirements submitted
            if has_req_uploads:
                req.status = RequestWorkflow.REQUIREMENTS_SUBMITTED
                if not req.requirements_submitted_at:
                    req.requirements_submitted_at = timezone.now()
                if not req.requirements_submission_note:
                    req.requirements_submission_note = 'Files imported from Supabase and marked as submitted by admin script.'
                req.save(update_fields=['status', 'requirements_submitted_at', 'requirements_submission_note'])

                RequestStatusHistory.objects.create(
                    request=req,
                    old_status=previous,
                    new_status=req.status,
                    changed_by='system',
                    notes='Automated: marked submitted because RequirementUpload records exist.'
                )

                try:
                    Notification.objects.create(
                        student=req.student,
                        request=req,
                        message=f"Requirements for request #{req.id} were recorded and marked as submitted."
                    )
                except Exception:
                    pass

                updated += 1
                self.stdout.write(self.style.SUCCESS(f'Updated Request {req.id}: {previous} -> {req.status}'))

        self.stdout.write(self.style.SUCCESS(f'Persist complete: scanned={total}, updated={updated}'))

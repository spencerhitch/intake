from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils.datastructures import MultiValueDict
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse_lazy
from django.contrib import messages

from django.http import HttpResponseNotFound, HttpResponse
from django.views.generic import View
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView



from django.core import mail

from intake import models, notifications, forms
from project.jinja2 import url_with_ids



class Home(TemplateView):
    template_name = "main_splash.jinja"


class MultiStepFormViewBase(FormView):
    session_storage_key = "form_in_progress"

    def dump_post_data_to_session(self):
        post_data = dict(self.request.POST.lists())
        self.request.session[self.session_storage_key] = post_data

    def load_post_data_from_session(self):
        data = self.request.session.get(self.session_storage_key, {})
        return MultiValueDict(data)


class MultiStepApplicationView(MultiStepFormViewBase):
    template_name = "apply_page.jinja"
    form_class = forms.FormSubmissionSerializer
    success_url = reverse_lazy('intake-thanks')
    error_message = _("There were some problems with your application. Please check the errors below.")

    def put_errors_in_flash_messages(self, form):
        for error in form.non_field_errors():
            messages.error(self.request, error)

    def form_invalid(self, form, *args, **kwargs):
        messages.error(self.request, self.error_message)
        self.put_errors_in_flash_messages(form)
        return super().form_invalid(form, *args, **kwargs)

    def confirmation(self, submission):
        flash_messages = submission.send_confirmation_notifications()
        for message in flash_messages:
            messages.success(self.request, message)

    def save_submission_and_send_notifications(self, form):
        submission = models.FormSubmission(answers=form.data)
        submission.save()
        number = models.FormSubmission.objects.count()
        notifications.slack_new_submission.send(
            submission=submission, request=self.request, submission_count=number)
        self.confirmation(submission)

    def form_valid(self, form):
        self.save_submission_and_send_notifications(form)
        return super().form_valid(form)


class Confirm(MultiStepApplicationView):
    '''Intended to provide a final acceptance of a form,
    after any necessary warnings have been raised.
    It follows the `Apply` view, which checks for warnings.
    '''
    incoming_message = _("Please double check the form. Some parts are empty and may cause delays.")

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        form_data = self.load_post_data_from_session()
        if form_data:
            form = self.form_class(data=form_data)
            # make sure the form has warnings.
            # trigger data cleaning
            form.is_valid()
            if form.warnings:
                messages.warning(self.request, self.incoming_message)
            context['form'] = form
        return context



class Apply(MultiStepApplicationView):
    '''The initial application page.
    Checks for warnings, and if they exist, redirects to a confirmation page.
    '''
    confirmation_url = reverse_lazy('intake-confirm')

    def form_valid(self, form):
        """If no errors, check for warnings, redirect to confirmation if needed
        """
        if form.warnings:
            # save the post data and move them to confirmation step
            self.dump_post_data_to_session()
            return redirect(self.confirmation_url)
        else:
            return super().form_valid(form)


class Thanks(TemplateView):
    template_name = "thanks.jinja"


class PrivacyPolicy(TemplateView):
    template_name = "privacy_policy.jinja"


class FilledPDF(View):

    def get(self, request, submission_id):
        submission = models.FormSubmission.objects.get(id=int(submission_id))
        fillable = models.FillablePDF.get_default_instance()
        pdf = fillable.fill(submission)
        # wrapper = FileWrapper(file(filename))
        # response = HttpResponse(wrapper, content_type='text/plain')
        # response['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(filename)
        # response['Content-Length'] = os.path.getsize(filename)
        # return response
        models.FormSubmission.mark_viewed([submission], request.user)
        return HttpResponse(pdf,
            content_type="application/pdf")


class ApplicationIndex(TemplateView):
    template_name = "app_index.jinja"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['submissions'] = models.FormSubmission.all_plus_related_objects()
        context['body_class'] = 'admin'
        return context


class Stats(TemplateView):
    template_name = "stats.jinja"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = {
            'received': models.FormSubmission.objects.count(),
            'opened': models.FormSubmission.get_opened_apps().count()
        }
        return context



class MultiSubmissionMixin:

    def get_ids_from_params(self, request):
        id_set = request.GET.get('ids')
        return [int(i) for i in id_set.split(',')]


class ApplicationBundle(View, MultiSubmissionMixin):
    def get(self, request):
        submission_ids = self.get_ids_from_params(request)
        submissions = list(models.FormSubmission.objects.filter(
            pk__in=submission_ids))
        models.FormSubmission.mark_viewed(submissions, request.user)
        return render(
            request,
            "app_bundle.jinja", {
                'submissions': submissions,
                'count': len(submissions),
                'app_ids': submission_ids
             })


class FilledPDFBundle(View, MultiSubmissionMixin):
    def get(self, request):
        submission_ids = self.get_ids_from_params(request)
        submissions = models.FormSubmission.objects.filter(
            pk__in=submission_ids)
        fillable = models.FillablePDF.get_default_instance()
        pdf = fillable.fill_many(submissions)
        return HttpResponse(pdf,
            content_type="application/pdf")


class Delete(View):
    template_name = "delete_page.jinja"
    def get(self, request, submission_id):
        submission = models.FormSubmission.objects.get(id=int(submission_id))
        return render(
            request,
            self.template_name, {'submission': submission})

    def post(self, request, submission_id):
        submission = models.FormSubmission.objects.get(id=int(submission_id))
        models.ApplicationLogEntry.objects.create(
            user=request.user,
            submission_id=submission_id,
            event_type=models.ApplicationLogEntry.DELETED
            )
        submission.delete()
        notifications.slack_submissions_deleted.send(
            submissions=[submission],
            user=request.user)
        return redirect(reverse_lazy('intake-app_index'))


class MarkSubmissionStepView(View, MultiSubmissionMixin):

    def get(self, request):
        submission_ids = self.get_ids_from_params(request)
        next_param = request.GET.get('next',
            reverse_lazy('intake-app_index'))
        models.ApplicationLogEntry.log_multiple(
            self.process_step, submission_ids, request.user)
        submissions = models.FormSubmission.objects.filter(pk__in=submission_ids)
        if hasattr(self, 'notification_function'):
            self.notification_function(
                submissions=list(submissions), user=request.user)
        return redirect(next_param)


class MarkProcessed(MarkSubmissionStepView):
    process_step = models.ApplicationLogEntry.PROCESSED
    notification_function = notifications.slack_submissions_processed.send


home = Home.as_view()
apply_form = Apply.as_view()
confirm = Confirm.as_view()
thanks = Thanks.as_view()
privacy = PrivacyPolicy.as_view()
stats = Stats.as_view()
filled_pdf = FilledPDF.as_view()
pdf_bundle = FilledPDFBundle.as_view()
app_index = ApplicationIndex.as_view()
app_bundle = ApplicationBundle.as_view()
mark_processed = MarkProcessed.as_view()
delete_page = Delete.as_view()


######## REDIRECT VIEWS ########
# for backwards compatibility

class PermanentRedirectView(View):
    '''Permanently redirects to a url
    by default, it will build a url from any kwargs
    self.build_redirect_url() can be overridden to provide logic
    '''
    redirect_view_name = None

    def build_redirect_url(self, request, **kwargs):
        return reverse_lazy(
            self.redirect_view_name,
            kwargs=dict(**kwargs))

    def get(self, request, **kwargs):
        redirect_url = self.build_redirect_url(request, **kwargs)
        return redirect(redirect_url, permanent=True)


class SingleIdPermanentRedirect(PermanentRedirectView):
    '''Redirects from 
        sanfrancisco/0efd75e8721c4308a8f3247a8c63305d/
    to
        application/3/
    '''
    def build_redirect_url(self, request, submission_id):
        submission = models.FormSubmission.objects.get(old_uuid=submission_id)
        return reverse_lazy(self.redirect_view_name,
            kwargs=dict(submission_id=submission.id)
            )


class MultiIdPermanentRedirect(PermanentRedirectView):
    '''Redirects from
        sanfrancisco/bundle/?keys=0efd75e8721c4308a8f3247a8c63305d|b873c4ceb1cd4939b1d4c890997ef29c
    to
        applications/bundle/?ids=3,4
    '''
    def build_redirect_url(self, request):
        key_set = request.GET.get('keys')
        uuids = [key for key in key_set.split('|')]
        submissions = models.FormSubmission.objects.filter(
            old_uuid__in=uuids)
        return url_with_ids(
            self.redirect_view_name,
            [s.id for s in submissions])









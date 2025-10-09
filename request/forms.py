"""
Forms for the request application.
"""

from django import forms
from accounts.models import Request, DocumentType, StudentAccount


class RequestForm(forms.ModelForm):
    """Form for creating new document requests"""
    
    class Meta:
        model = Request
        fields = ['document', 'purpose', 'copies']
        widgets = {
            'document': forms.Select(attrs={
                'class': 'form-select',
                'id': 'documentTypeSelect'
            }),
            'purpose': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'State the purpose of request',
                'maxlength': 500
            }),
            'copies': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10,
                'value': 1
            })
        }
        labels = {
            'document': 'Document Type',
            'purpose': 'Purpose of Request',
            'copies': 'Number of Copies'
        }
        help_texts = {
            'copies': 'Maximum of 10 copies allowed per request.',
            'purpose': 'Please provide a detailed purpose for your request (minimum 10 characters).'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set queryset for document field
        self.fields['document'].queryset = DocumentType.objects.all()
        self.fields['document'].empty_label = "Select Document Type"
    
    def clean_copies(self):
        copies = self.cleaned_data.get('copies')
        if copies and (copies < 1 or copies > 10):
            raise forms.ValidationError("Number of copies must be between 1 and 10.")
        return copies
    
    def clean_purpose(self):
        purpose = self.cleaned_data.get('purpose')
        if purpose and len(purpose.strip()) < 10:
            raise forms.ValidationError("Purpose must be at least 10 characters long.")
        return purpose.strip() if purpose else purpose


class RequestFilterForm(forms.Form):
    """Form for filtering requests"""
    
    STATUS_CHOICES = [
        ('', 'All Statuses'),
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]
    
    SORT_CHOICES = [
        ('-date_requested', 'Newest First'),
        ('date_requested', 'Oldest First'),
        ('document__name', 'Document Type A-Z'),
        ('-document__name', 'Document Type Z-A'),
        ('status', 'Status A-Z'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    document_type = forms.ModelChoiceField(
        queryset=DocumentType.objects.all(),
        required=False,
        empty_label="All Document Types",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial='-date_requested',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class RequestCommentForm(forms.Form):
    """Form for adding comments to requests"""
    
    comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Add a comment or note...',
            'maxlength': 1000
        }),
        max_length=1000,
        label='Comment'
    )
    
    def clean_comment(self):
        comment = self.cleaned_data.get('comment')
        if comment and len(comment.strip()) < 5:
            raise forms.ValidationError("Comment must be at least 5 characters long.")
        return comment.strip() if comment else comment


class RequestCancellationForm(forms.Form):
    """Form for cancelling requests"""
    
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Please provide a reason for cancellation...',
            'maxlength': 500
        }),
        max_length=500,
        required=False,
        label='Reason for Cancellation'
    )
    
    confirm = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='I confirm that I want to cancel this request'
    )


class BulkRequestForm(forms.Form):
    """Form for submitting multiple requests at once"""
    
    documents = forms.ModelMultipleChoiceField(
        queryset=DocumentType.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label='Select Documents'
    )
    
    purpose = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'State the purpose for all selected documents',
            'maxlength': 500
        }),
        max_length=500,
        label='Purpose (applies to all documents)'
    )
    
    copies_per_document = forms.IntegerField(
        min_value=1,
        max_value=5,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,
            'max': 5
        }),
        label='Copies per Document',
        help_text='Number of copies for each selected document (max 5 for bulk requests)'
    )
    
    def clean_documents(self):
        documents = self.cleaned_data.get('documents')
        if not documents:
            raise forms.ValidationError("Please select at least one document.")
        if len(documents) > 5:
            raise forms.ValidationError("Maximum of 5 documents allowed in bulk request.")
        return documents
    
    def clean_purpose(self):
        purpose = self.cleaned_data.get('purpose')
        if purpose and len(purpose.strip()) < 15:
            raise forms.ValidationError("Purpose for bulk requests must be at least 15 characters long.")
        return purpose.strip() if purpose else purpose
from django import forms
from .models import Dataset
from .preprocess import load_and_clean


class DatasetForm(forms.ModelForm):
    class Meta:
        model = Dataset
        fields = ['name', 'file']
        labels = {'name': 'Product name', 'file': 'Sales CSV file'}

    def clean_file(self):
        f = self.cleaned_data['file']
        if not f.name.lower().endswith('.csv'):
            raise forms.ValidationError('Please upload a .csv file.')
        try:
            load_and_clean(f)
        except ValueError as e:
            raise forms.ValidationError(str(e))
        except Exception:
            raise forms.ValidationError('Could not read this file. Is it a valid CSV?')
        f.seek(0)
        return f
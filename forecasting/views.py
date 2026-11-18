import csv
import math

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from . import eda, forecast_models
from .forms import DatasetForm
from .models import Dataset, ForecastRun, ForecastPoint
from .preprocess import load_and_clean


@login_required
def home(request):
    datasets = request.user.datasets.order_by('-uploaded_at')
    return render(request, 'forecasting/home.html', {'datasets': datasets})


@login_required
def upload(request):
    if request.method == 'POST':
        form = DatasetForm(request.POST, request.FILES)
        if form.is_valid():
            dataset = form.save(commit=False)
            dataset.user = request.user
            dataset.save()
            messages.success(request, 'File uploaded and cleaned successfully.')
            return redirect('dataset_detail', pk=dataset.pk)
    else:
        form = DatasetForm()
    return render(request, 'forecasting/upload.html', {'form': form})


@login_required
def dataset_detail(request, pk):
    dataset = get_object_or_404(Dataset, pk=pk, user=request.user)
    df, report = load_and_clean(dataset.file.path)

    preview = df.head(12).copy()
    preview['date'] = preview['date'].dt.strftime('%b %Y')

    context = {
        'dataset': dataset,
        'report': report,
        'preview_html': preview.round(2).to_html(
            index=False, classes='table table-sm table-striped'),
        'stats_html': df.drop(columns='date').describe().round(2).to_html(
            classes='table table-sm table-bordered'),
    }
    return render(request, 'forecasting/dataset_detail.html', context)


@login_required
def dataset_eda(request, pk):
    dataset = get_object_or_404(Dataset, pk=pk, user=request.user)
    df, report = load_and_clean(dataset.file.path)
    context = {
        'dataset': dataset,
        'report': report,
        'stats': eda.key_stats(df),
        'driver': eda.top_driver(df),
        'charts': eda.build_charts(df),
    }
    return render(request, 'forecasting/eda.html', context)


def _clean_number(value):
    """Convert NaN to None so the database accepts it."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    return float(value)


@login_required
def run_forecast(request, pk):
    dataset = get_object_or_404(Dataset, pk=pk, user=request.user)
    if request.method != 'POST':
        return redirect('forecast', pk=pk)

    df, _ = load_and_clean(dataset.file.path)
    results = forecast_models.run_all(df)

    dataset.runs.all().delete()          # replace any older results
    for r in results:
        run = ForecastRun.objects.create(
            dataset=dataset,
            model_name=r['name'],
            mae=r.get('mae'),
            rmse=r.get('rmse'),
            mape=r.get('mape'),
            is_best=r.get('is_best', False),
            error=r.get('error', ''),
        )
        for kind in ('test', 'future'):
            if kind not in r:
                continue
            ForecastPoint.objects.bulk_create([
                ForecastPoint(run=run, kind=kind, date=row.date.date(),
                              predicted=_clean_number(row.predicted),
                              lower=_clean_number(row.lower),
                              upper=_clean_number(row.upper))
                for row in r[kind].itertuples()
            ])

    failed = [r['name'] for r in results if r['error']]
    if failed:
        messages.warning(request, f"These models could not run: {', '.join(failed)}.")
    else:
        messages.success(request, 'Forecast complete.')
    return redirect('forecast', pk=pk)


@login_required
def forecast(request, pk):
    dataset = get_object_or_404(Dataset, pk=pk, user=request.user)
    runs = list(dataset.runs.order_by('mape'))
    context = {'dataset': dataset, 'runs': runs}

    good_runs = [r for r in runs if not r.error]
    if good_runs:
        df, _ = load_and_clean(dataset.file.path)
        best = next((r for r in good_runs if r.is_best), good_runs[0])
        context.update({
            'best': best,
            'best_points': best.points.filter(kind='future'),
            'forecast_chart': forecast_models.forecast_chart(df, good_runs),
            'test_chart': forecast_models.test_chart(df, good_runs),
            'assumed': forecast_models.future_factors(df).iloc[0].drop('date').round(2).to_dict(),
        })
    return render(request, 'forecasting/forecast.html', context)


@login_required
def download_forecast(request, pk):
    dataset = get_object_or_404(Dataset, pk=pk, user=request.user)
    runs = dataset.runs.filter(error='')

    response = HttpResponse(content_type='text/csv')
    filename = f"{dataset.name.replace(' ', '_')}_forecast.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(['month', 'model', 'best_model', 'predicted', 'lower', 'upper'])
    for run in runs:
        for p in run.points.filter(kind='future'):
            writer.writerow([p.date.strftime('%Y-%m'), run.model_name,
                             'yes' if run.is_best else 'no',
                             round(p.predicted), round(p.lower or 0), round(p.upper or 0)])
    return response

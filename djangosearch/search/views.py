from .models import Search
from django.shortcuts import render, get_object_or_404
from django.shortcuts import redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import time

def search(request):
    time_start = time.time()
    search = ""    
    result_search = ""
    results = ""
    length_result_search = 0
    if request.method == "GET":
        search = request.GET.get('q')
        if search is not None and search != '':
            result_search = Search.objects.filter(title__icontains = search) | Search.objects.filter(h1__icontains = search) | Search.objects.filter(h2__icontains = search) | Search.objects.filter(h3__icontains = search) | Search.objects.filter(h4__icontains = search) | Search.objects.filter(h5__icontains = search) | Search.objects.filter(h6__icontains = search)  # __icontains не чувствительна к регистру
            
        length_result_search = len(result_search)
        for line in result_search:
            if line.title != 'None' and line.title != "['']":
                line.title = line.title[2:-2].replace("\', \'", " ")
            if line.h1 != 'None' and line.h1 != "['']":
                line.h1 = line.h1[2:-2].replace("\', \'", " ")
            if line.h2 != 'None' and line.h2 != "['']":
                line.h2 = line.h2[2:-2].replace("\', \'", " ")
            if line.h3 != 'None' and line.h3 != "['']":
                line.h3 = line.h3[2:-2].replace("\', \'", " ")
            if line.h4 != 'None' and line.h4 != "['']":
                line.h4 = line.h4[2:-2].replace("\', \'", " ")
            if line.h5 != 'None' and line.h5 != "['']":
                line.h5 = line.h5[2:-2].replace("\', \'", " ")
            if line.h6 != 'None' and line.h6 != "['']":
                line.h6 = line.h6[2:-2].replace("\', \'", " ")  
    
        last_question = '?q=%s' % search
        current_page = Paginator(result_search, 10)
    
        page = request.GET.get('page')
        try:
            results = current_page.page(page)
        except PageNotAnInteger:
            results = current_page.page(1)
        except EmptyPage:
            results = current_page.page(current_page.num_pages)

    time_stop = round(time.time() - time_start, 2)
    return render(request, 'search/search.html', {'search': search, 'length_result_search': length_result_search, 'page': page, 'results': results, 'last_question': last_question, 'time_stop': time_stop})

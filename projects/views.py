from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Project, ProjectConnection

def project_list(request):
    """Public list of published projects."""
    projects = Project.objects.filter(status='Published').order_by('-created_at')
    return render(request, 'projects/list.html', {'projects': projects})

@login_required
def project_create(request):
    """Create a new project."""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        status = request.POST.get('status', 'Draft')
        image = request.FILES.get('image')

        project = Project.objects.create(
            owner=request.user,
            title=title,
            description=description,
            status=status,
            image=image
        )
        messages.success(request, f"Project '{title}' created successfully!")
        return redirect('projects:detail', project_id=project.id)

    return render(request, 'projects/create.html')

def project_detail(request, project_id):
    """Project details and collaboration management."""
    project = get_object_or_404(Project, id=project_id)
    
    # Check visibility
    if project.status == 'Draft' and project.owner != request.user:
        messages.error(request, "This project is a draft and only visible to the owner.")
        return redirect('projects:list')

    is_connected = False
    if request.user.is_authenticated:
        is_connected = ProjectConnection.objects.filter(project=project, user=request.user).exists()

    connections = project.connections.all() if project.owner == request.user else None

    return render(request, 'projects/detail.html', {
        'project': project,
        'is_connected': is_connected,
        'connections': connections
    })

@login_required
def connect_to_project(request, project_id):
    """Join or support a project."""
    project = get_object_or_404(Project, id=project_id, status='Published')
    
    if project.owner == request.user:
        messages.warning(request, "You are the owner of this project.")
        return redirect('projects:detail', project_id=project.id)

    connection, created = ProjectConnection.objects.get_or_create(
        project=project,
        user=request.user
    )
    
    if created:
        messages.success(request, f"You have successfully connected with '{project.title}'!")
    else:
        messages.info(request, "You are already connected to this project.")
        
    return redirect('projects:detail', project_id=project.id)

@login_required
def project_edit(request, project_id):
    """Edit project details or status."""
    project = get_object_or_404(Project, id=project_id, owner=request.user)
    
    if request.method == 'POST':
        project.title = request.POST.get('title', project.title)
        project.description = request.POST.get('description', project.description)
        project.status = request.POST.get('status', project.status)
        if request.FILES.get('image'):
            project.image = request.FILES.get('image')
        project.save()
        messages.success(request, "Project updated successfully!")
        return redirect('projects:detail', project_id=project.id)

    return render(request, 'projects/edit.html', {'project': project})

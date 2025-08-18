import os
import shutil

from flask import Blueprint, request
from flask import redirect, url_for, flash
from flask import render_template

from models import db, Project

project_bp = Blueprint('project', __name__)


@project_bp.route('/project/create', methods=['POST'])
def create_project():
    name = request.form.get('name')
    description = request.form.get('description')

    if not name:
        flash('项目名称不能为空', 'error')
        return redirect(url_for('main.index'))

    project = Project(name=name, description=description)
    db.session.add(project)
    db.session.commit()

    flash(f'项目 "{name}" 创建成功', 'success')
    return redirect(url_for('main.project_detail', project_id=project.id))


@project_bp.route('/project/<int:project_id>')
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    return render_template('project_detail.html', project=project)


@project_bp.route('/project/<int:project_id>/delete', methods=['POST'])
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    project_name = project.name

    # 删除项目相关的所有文件
    project_path = os.path.join('data/datasets', str(project_id))
    if os.path.exists(project_path):
        shutil.rmtree(project_path)

    # 删除项目记录
    db.session.delete(project)
    db.session.commit()

    flash(f'项目 "{project_name}" 已删除', 'success')
    return redirect(url_for('main.index'))

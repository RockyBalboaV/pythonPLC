from fabric.api import local, env, run, sudo, cd

env.hosts = ['yakumo17s:touhou@104.160.41.99:9999']


def test():
    local('python -m unittest discover')


def upgrade_libs():
    sudo('apt-get update')
    sudo('apt-get upgrade')


def setup():
    test()
    upgrade_libs()

    sudo('apt-get install -y build-essential')
    sudo('apt-get install -y git')
    sudo('apt-get install -y python')
    sudo('apt-get install -y python-pip')
    sudo('apt-get install -y python-all-dev')
    sudo('apt-get install -y nginx')

    # sudo('useradd -d /home/deploy/ deploy')
    # sudo('gpasswd -a deploy sudo')

    # sudo('chown -R deploy /usr/local')
    # sudo('chown -R deploy /usr/lib/python2.7')

    run('git config --global credential.helper store')

    with cd('/home/yakumo17s/'):
        run('git clone https://github.com/RockyBalboaV/pythonPLC.git')

    with cd('/home/yakumo17s/pythonPLC/WebServer'):
        run('pip install -r requirements.txt')
        run('python manage.py createdb')


def deploy():
    test()
    upgrade_libs()
    with cd('/home/yakumo17s/pythonPLC/WebServer'):
        run('git pull')
        run('pip install -r requirements.txt')
        sudo('cp supervisor.conf /etc/supervisor/conf.d/web_server.conf')
        sudo('cp nginx.conf /etc/nginx/sites-available/python_plc')
        sudo('ln -sf /etc/nginx/sites-available/python-plc')

    sudo('service supervisor restart')
    sudo('service nginx restart')

from fabric.api import local, env, run, sudo, cd

env.hosts = ['pi:raspberry@192.168.18.135']


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
    sudo('apt-get install -y supervisor')

    # sudo('useradd -d /home/deploy/ deploy')
    # sudo('gpasswd -a deploy sudo')

    # sudo('chown -R deploy /usr/local')
    # sudo('chown -R deploy /usr/lib/python2.7')

    run('git config --global credential.helper store')

    with cd('/home/yakumo17s/deploy'):
        run('git clone https://github.com/RockyBalboaV/pythonPLC.git')

    with cd('/home/yakumo17s/deploy/pythonPLC/WebServer'):
        run('pip install -r requirements.txt')
        run('python manage.py createdb')

    run('python app.py --reset true')


def deploy():
    test()
    upgrade_libs()
    with cd('/home/yakumo17s/deploy/pythonPLC/WebServer'):
        run('git pull')
        run('pip install -r requirements.txt')
        sudo('cp supervisord.conf /etc/supervisor/conf.d/app.conf')
        run('python app.py --start true')

    sudo('service supervisor restart')

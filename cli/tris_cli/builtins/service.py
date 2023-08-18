from trisigma import command

colors = {
    'UP': '\033[92m',
    'UP(?)': '\033[92m',
    'DOWN': '\033[91m',
    'DOWN*': '\033[91m',
    'PAUSED': '\033[93m',
    'STOPPED': '\033[90m',
}
endcolor = '\033[0m'

@command.expose('service')
def cmd_service (service_name: str, target: str):
    """Displays detailed service information and it's workflows"""

    from trisigma import repo
    import timeago
    from datetime import datetime
    from trisigma import entity
    repository = repo.ServiceRepositoryMongo()
    service = entity.Service(service_name, target)
    service_details = repository.get_service_details(service)
    if service_details is None:
        print('Service not found')
        return
    workflow_details = repository.get_all_workflow_details(service)
    #service title
    title_line = 'Service: {0} ({1})'.format(service.name, service.target)
    print(title_line)
    #service status
    status = determine_service_status(service_details)
    status_line = 'Status: {color}{status}{endcolor}'.format(
        color = colors[status],
        status = status,
        endcolor = endcolor)
    print(status_line)
    #workflows
    if len(workflow_details) == 0:
        print('No workflows declared')
        return
    wf_by_status = {'UP': [], 'DOWN': [], 'PAUSED': [], 'STOPPED': []}
    for wf in workflow_details:
        wf_color = colors[wf['status']] if status in ['UP', 'UP(?)'] else colors[status]
        wf_created_at = datetime.fromtimestamp(
                wf['created_at']
            ).strftime('%m/%d/%Y (%H:%M:%S)')
        wf_last_beat = timeago.format(datetime.fromtimestamp(wf['last_progress']), datetime.now())
        wf_line = '* {color}{name}{endcolor} - creation: {created_at} - progress: {last_beat}'.format(
            color = wf_color,
            name = wf['name'],
            endcolor = endcolor,
            created_at = wf_created_at,
            last_beat = wf_last_beat
        )
        wf_by_status[wf['status']].append(wf_line)
    wf_status_title = ''
    wf_lines = []
    for status, wfs in wf_by_status.items():
        if len(wfs) == 0: continue
        wf_status_title += "{status}:{count} ".format(
            status = status,
            count = len(wfs))
        wf_lines += wfs
    wf_title_bar = 'Workflows ({wf_status_title})'.format(
        wf_status_title = wf_status_title[:-1])
    print(wf_title_bar)
    for wf_line in wf_lines:
        print(wf_line)


@command.expose('status')
def cmd_service_stats():
    """Lists all services and their status"""
    from trisigma import repo
    import timeago
    from datetime import datetime

    repository = repo.ServiceRepositoryMongo()
    details = repository.get_all_service_details()
    if len(details) == 0:
        print('No services found')
        return
    titlebar= '  {0:8} {1:25} {2:18} {3:25} {4:15}'.format(
        'STATUS', 'SERVICE', 'TARGET', 'CREATED AT', 'LAST HEARTBEAT')
    lc = '-'
    lines= '  {0:8} {1:25} {2:15} {3:25} {4:15}'.format(
        lc*8, lc*25, lc*18, lc*25, lc*15)
    print(titlebar)
    print(lines)

    for det in details:
        try:
            name = _get_compressed_name(det['name'], 25)
            target = _get_compressed_name(det['target'], 18)
            status = determine_service_status(det)
            created_at_dt = datetime.fromtimestamp(
                    det['created_at']
                ).strftime('%m/%d/%Y (%H:%M:%S)')
            created_at_ago = timeago.format(
                datetime.fromtimestamp(det['created_at']), datetime.now())
            #created_at = '{0} ({1})'.format(created_at_dt, created_at_ago)
            created_at = created_at_dt

            last_heartbeat = timeago.format(
                datetime.fromtimestamp(det['last_heartbeat']), datetime.now())

            line = '* {color}{0:8}{endcolor} {1:25} {2:18} {3:25} {4:15}'.format(
                status, name, target, created_at, last_heartbeat,
                color=colors[status], endcolor=endcolor)
        except Exception as e:
            msg = 'Error: {0}'.format(e)
            line = msg
        print(line)

def _get_compressed_name(name, size):
    if len(name) <= size:
        return name
    mid = size // 2
    inc = 0 if size % 2 == 0 else 1
    return name[:mid-1] + '...' + name[-(mid+inc)+2:]

@command.expose('remove-all-services')
def cmd_remove_all_services():
    """Clears all services"""
    print('Warning: This will remove all services. Enter "removeall" to proceed...')
    if not 'removeall' == input('> '):
        print('Aborted.')
        return
    from trisigma import repo
    from trisigma import entity
    repository = repo.ServiceRepositoryMongo()
    services = repository.get_all_service_details()
    if len(services) == 0:
        print('No services to clear.')
        return
    for service_det in services:
        service = entity.Service(service_det['name'], service_det['target'])
        print('Deleting {0}...\t'.format(service.name), end='')
        repository.remove_service(service)
        print('Done.')
    print('All services cleared.')

@command.expose('remove-service')
def cmd_remove_services(service_name, target):
    """Clears all services"""
    print(f"Warning: Service {service_name}'s {target} instance "
        + "is about to be removed. Enter \"remove\" to proceed...")
    if not 'remove' == input('> '):
        print('Aborted.')
        return
    from trisigma import repo
    from trisigma import entity
    repository = repo.ServiceRepositoryMongo()
    service = entity.Service(service_name, target)
    if not repository.service_exists(service):
        print('Service does not exist.\nAborted.')
        return
    print('Deleting {0}...\t'.format(service.name), end='')
    repository.remove_service(service)
    print('Done.')


def determine_service_status(service_details):
    from datetime import datetime
    det = service_details
    if det['status'] == 'UP':
        if 'beat_timeout' in det['meta'].keys():
            last_beat = datetime.fromtimestamp(det['last_heartbeat'])
            now = datetime.now()
            diff = now - last_beat
            if diff.seconds > det['meta']['beat_timeout']:
                status = 'DOWN*'
            else:
                status = 'UP'
        else:
            status = 'UP(?)'
    else:
        status = det['status']
    return status



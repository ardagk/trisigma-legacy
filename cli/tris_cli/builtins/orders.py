from trisigma import command

@command.expose('oreq')
def get_order_requests(label, instrument=None):
    from trisigma import repo
    order_repo = repo.OrderRepositoryMongo()
    reqs = order_repo.get_order_requests(label=label, instrument=instrument)
    if not reqs:
        print('No order requests found for label: %s' % label)
        return
    [print(str(req)) for req in reqs]



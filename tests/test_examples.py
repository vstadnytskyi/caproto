import signal
import os
import time
from multiprocessing import Process
import curio


def test_synchronous_client():
    from caproto.examples.synchronous_client import main

    pid = os.getpid()

    def sigint(delay):
        time.sleep(delay)
        # By now the example should be subscribed and waiting for Ctrl+C.
        os.kill(pid, signal.SIGINT)

    p = Process(target=sigint, args=(2,))
    p.start()
    main()
    p.join()


def test_curio_client():
    from caproto.examples.curio_client import main
    main()


def test_curio_server(kernel):
    import caproto.examples.curio_server as server
    import caproto.examples.curio_client as client

    async def run_server():
        pvdb = ["pi"]
        ctx = server.Context('0.0.0.0', 5064, pvdb)
        await ctx.run()

    async def run_client():
        # Some user function to call when subscriptions receive data.
        called = []
        def user_callback(command):
            print("Subscription has received data.")
            called.append(True)

        ctx = client.Context()
        await ctx.register()
        await ctx.search('pi')
        chan1.register_user_callback(user_callback)
        # ...and then wait for all the responses.
        await chan1.wait_for_connection()
        reading = await chan1.read()
        print('reading:', reading)
        await chan1.subscribe()
        await chan1.unsubscribe(0)
        await chan1.write((5,))
        reading = await chan1.read()
        print('reading:', reading)
        await chan1.write((6,))
        reading = await chan1.read()
        print('reading:', reading)
        await chan1.clear()
        assert called

    async def task():
        server_task = await curio.spawn(run_server())
        await curio.sleep(5)
        client_task = await curio.spawn(run_client())
        await client_task.join()
        await kernel_task.kill()

    curio.run(task())
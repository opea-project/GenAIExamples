import asyncio
import signal
import time
from typing import Optional, Dict
from logger import CustomLogger
from utils import check_ports_availability


# Define the signals that will be handled by the AsyncLoop class
HANDLED_SIGNALS = (
    signal.SIGINT,  # Unix signal 2. Sent by Ctrl+C.
    signal.SIGTERM,  # Unix signal 15. Sent by `kill <pid>`.
    signal.SIGSEGV,  # Unix signal 11. Caused by an invalid memory reference.
)


class AsyncLoop:
    """
    Async loop to run a microservice asynchronously.
    This class is designed to handle the running of a microservice in an asynchronous manner.
    It sets up an event loop and handles certain signals to gracefully stop the service.
    """

    def __init__(self, args: Optional[Dict] = None) -> None:
        """
        Initialize the AsyncLoop class.
        This method sets up the initial state of the AsyncLoop, including setting up the event loop and signal handlers.
        """
        self.args = args
        if args.get('name', None):
            self.name = f'{args.get("name")}/{self.__class__.__name__}'
        else:
            self.name = self.__class__.__name__
        self.protocol = args.get('protocol', 'http')
        self.host = args.get('host', 'localhost')
        self.port = args.get('port', 8080)
        self.quiet_error = args.get('quiet_error', False)
        self.logger = CustomLogger(self.name)
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self.is_cancel = asyncio.Event()
        self.logger.info(f'Setting signal handlers')

        def _cancel(signum, frame):
            """
            Signal handler for the AsyncLoop class.
            This method is called when a signal is received. It sets the is_cancel event to stop the event loop.
            """
            self.logger.info(f'Received signal {signum}')
            self.is_cancel.set(),

        for sig in HANDLED_SIGNALS:
            signal.signal(sig, _cancel)

        self._start_time = time.time()
        self._loop.run_until_complete(self.async_setup())

    def run_forever(self):
        """
        Running method to block the main thread.
        This method runs the event loop until a Future is done. It is designed to be called in the main thread to keep it busy.
        """
        self._loop.run_until_complete(self._loop_body())

    def teardown(self):
        """
        Call async_teardown() and stop and close the event loop.
        This method is responsible for tearing down the event loop. It first calls the async_teardown method to perform
        any necessary cleanup, then it stops and closes the event loop. It also logs the duration of the event loop.
        """
        self._loop.run_until_complete(self.async_teardown())
        self._loop.stop()
        self._loop.close()
        self._stop_time = time.time()
        self.logger.info(f"Async loop is tore down. Duration: {self._stop_time - self._start_time}")

    def _get_server(self):
        """
        Get the server instance based on the protocol.
        This method currently only supports HTTP services. It creates an instance of the HTTPService class with the
        necessary arguments. 
        In the future, it will also support gRPC services.
        """
        if self.protocol.lower() == 'http':
            from http_service import HTTPService

            runtime_args = self.args.get('runtime_args', None)
            runtime_args['protocol'] = self.protocol
            runtime_args['host'] = self.host
            runtime_args['port'] = self.port
            return HTTPService(
                uvicorn_kwargs=self.args.get('uvicorn_kwargs', None),
                runtime_args=runtime_args,
                cors=self.args.get('cors', None),
            )

    async def async_setup(self):
        """
        The async method setup the runtime.
        This method is responsible for setting up the server. It first checks if the port is available, then it gets
        the server instance and initializes it.
        """
        if not (check_ports_availability(self.host, self.port)):
            raise RuntimeError(f'port:{self.port}')

        self.server = self._get_server()
        await self.server.initialize_server()

    async def async_run_forever(self):
        """
        Running method of the server.
        """
        await self.server.execute_server()

    async def async_teardown(self):
        """
        Terminate the server.
        """
        await self.server.terminate_server()

    async def _wait_for_cancel(self):
        """
        Wait for the cancellation event.
        This method waits for the is_cancel event to be set. If the server has a _should_exit attribute, it will also
        wait for that to be True. Once either of these conditions is met, it will call the async_teardown method.
        """
        if isinstance(self.is_cancel, asyncio.Event) and not hasattr(
            self.server, '_should_exit'
        ):
            await self.is_cancel.wait()
        else:
            while not self.is_cancel.is_set() and not getattr(
                self.server, '_should_exit', False
            ):
                await asyncio.sleep(0.1)

        await self.async_teardown()

    async def _loop_body(self):
        """
        The main body of the event loop.
        This method runs the async_run_forever and _wait_for_cancel methods concurrently. If a CancelledError is raised,
        it logs a warning message.
        """
        try:
            await asyncio.gather(self.async_run_forever(), self._wait_for_cancel())
        except asyncio.CancelledError:
            self.logger.warning('received terminate ctrl message from main process')

    def __enter__(self):
        """
        Enter method for the context manager.
        This method simply returns the instance itself.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit method for the context manager.
        This method handles any exceptions that occurred within the context. If a KeyboardInterrupt was raised, it logs
        an info message. If any other exception was raised, it logs an error message. Finally, it attempts to call the
        teardown method. If an OSError is raised during this, it is ignored. Any other exceptions are logged as errors.
        """
        if exc_type == KeyboardInterrupt:
            self.logger.info(f'{self!r} is interrupted by user')
        elif exc_type and issubclass(exc_type, Exception):
            self.logger.error(
                (
                    f'{exc_val!r} during {self.run_forever!r}'
                    + f'\n add "--quiet-error" to suppress the exception details'
                    if not self.quiet_error
                    else ''
                ),
                exc_info=not self.quiet_error,
            )
        else:
            self.logger.info(f'{self!r} is ended')

        return True

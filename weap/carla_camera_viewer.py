"""Display a chase camera for CARLA's hero vehicle"""
import argparse
import queue
import time

import carla
import numpy as np
import pygame


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', type=int, default=2000)
    parser.add_argument('--width', type=int, default=800)
    parser.add_argument('--height', type=int, default=450)
    args = parser.parse_args()
    client = carla.Client(args.host, args.port)
    client.set_timeout(5.0)
    pygame.init()
    screen = pygame.display.set_mode((args.width, args.height))
    pygame.display.set_caption('CARLA chase camera — waiting for hero vehicle')
    clock = pygame.time.Clock()
    frames = queue.Queue(maxsize=1)
    camera = None
    vehicle = None
    last_poll = 0.0

    def receive(image):
        try:
            frames.get_nowait()
        except queue.Empty:
            pass
        try:
            frames.put_nowait(image)
        except queue.Full:
            pass

    def stop_camera():
        nonlocal camera
        if camera is not None:
            try:
                camera.stop()
                camera.destroy()
            except RuntimeError:
                pass
            camera = None
        while not frames.empty():
            try:
                frames.get_nowait()
            except queue.Empty:
                break

    try:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False
            if not running:
                break
            if time.monotonic() - last_poll > 1.0:
                last_poll = time.monotonic()
                try:
                    world = client.get_world()
                    heroes = [a for a in world.get_actors().filter('vehicle.*')
                              if a.attributes.get('role_name') in ('hero', 'ego_vehicle')]
                    hero = heroes[0] if heroes else None
                    if (camera is not None and not camera.is_alive) or (vehicle is not None and (hero is None or hero.id != vehicle.id)):
                        stop_camera()
                        vehicle = None
                    if camera is None and hero is not None:
                        bp = world.get_blueprint_library().find('sensor.camera.rgb')
                        bp.set_attribute('image_size_x', str(args.width))
                        bp.set_attribute('image_size_y', str(args.height))
                        bp.set_attribute('fov', '90')
                        bp.set_attribute('sensor_tick', '0.1')
                        camera = world.spawn_actor(bp, carla.Transform(
                            carla.Location(x=-6.0, z=3.0), carla.Rotation(pitch=-15)), attach_to=hero)
                        vehicle = hero
                        camera.listen(receive)
                        pygame.display.set_caption('CARLA chase camera — Esc to close')
                    elif hero is None:
                        pygame.display.set_caption('CARLA chase camera — waiting for hero vehicle')
                except RuntimeError as exc:
                    print(f'Waiting for CARLA: {exc}', flush=True)
                    stop_camera()
                    vehicle = None
            try:
                frame = frames.get_nowait()
                rgb = np.frombuffer(frame.raw_data, dtype=np.uint8).reshape(frame.height, frame.width, 4)[:, :, :3][:, :, ::-1]
                screen.blit(pygame.surfarray.make_surface(rgb.swapaxes(0, 1)), (0, 0))
                pygame.display.flip()
            except queue.Empty:
                pass
            clock.tick(30)
    finally:
        stop_camera()
        pygame.quit()


if __name__ == '__main__':
    main()

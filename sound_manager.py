import pygame
import numpy as np

class SpaceAudio:
    def __init__(self):
        # Pre-initialize mixer for zero latency
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.mixer.init()
        
        # Generate procedural sounds
        self.paddle_sound = self._synthesize(frequency=440, duration=0.1, wave_type='square')
        self.wall_sound = self._synthesize(frequency=220, duration=0.1, wave_type='sine')
        self.score_sound = self._synthesize(frequency=880, duration=0.3, wave_type='sine')
        self.win_sound = self._synthesize(frequency=1200, duration=0.6, wave_type='square')

    def _synthesize(self, frequency, duration, wave_type='sine', volume=0.3):
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        buf = np.zeros((n_samples, 2), dtype=np.int16)
        max_amp = 32767 * volume
        
        for s in range(n_samples):
            t = float(s) / sample_rate
            if wave_type == 'sine':
                val = int(max_amp * np.sin(2 * np.pi * frequency * t))
            else: # square wave for retro feel
                val = int(max_amp * np.sign(np.sin(2 * np.pi * frequency * t)))
            buf[s][0] = val # Left channel
            buf[s][1] = val # Right channel
            
        return pygame.sndarray.make_sound(buf)

    # Trigger Methods
    def play_paddle(self): self.paddle_sound.play()
    def play_wall(self): self.wall_sound.play()
    def play_score(self): self.score_sound.play()
    def play_win(self): self.win_sound.play()
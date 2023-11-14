import math
from pyaudio import PyAudio, paUInt8


def generate_sine_wave(frequency, duration, volume=0.2, sample_rate=22050):
    ''' Generate a tone at the given frequency.

        Limited to unsigned 8-bit samples at a given sample_rate.
        The sample rate should be at least double the frequency.
    '''
    if sample_rate < (frequency * 2):
        print('Warning: sample_rate must be at least double the frequency '
              f'to accurately represent it:\n    sample_rate {sample_rate}'
              f' ≯ {frequency*2} (frequency {frequency}*2)')

    num_samples = int(sample_rate * duration)
    #print(f"num_samples {num_samples}")
    rest_frames = num_samples % sample_rate

    pa = PyAudio()
    stream = pa.open(
        format=paUInt8,
        channels=1,  # mono
        rate=sample_rate,
        output=True,
    )

    # make samples
    def s(i): return volume * math.sin(2 *
                                       math.pi * frequency * i / sample_rate)
    # print(f"New Samples {(s(i))}")
    samples = (int(s(t) * 0x7f + 0x80) for t in range(num_samples))
    stream.write(bytes(bytearray(samples)))

    # fill remainder of frameset with silence
    #stream.write(b'\x80' * rest_frames)

    stream.stop_stream()
    stream.close()
    pa.terminate()


#generate_sine_wave(400, 1)

from distutils.command.build import build
import random
import numpy as np
import matplotlib.pyplot as plt
import librosa
import librosa.display


# class that uses the librosa library to analyze the key that an mp3 is in arguments: waveform: an mp3 file loaded by
# librosa, ideally separated out from any percussive sources sr: sampling rate of the mp3, which can be obtained when
# the file is read with librosa tstart and tend: the range in seconds of the file to be analyzed; default to the
# beginning and end of file if not specified


class Tonal_Fragment(object):
    def __init__(self, waveform, sr, tstart=None, tend=None):
        self.waveform = waveform
        self.sr = sr
        self.tstart = tstart
        self.tend = tend

        if self.tstart is not None:
            self.tstart = librosa.time_to_samples(self.tstart, sr=self.sr)
        if self.tend is not None:
            self.tend = librosa.time_to_samples(self.tend, sr=self.sr)
        self.y_segment = self.waveform[self.tstart:self.tend]
        self.chromograph = librosa.feature.chroma_cqt(y=self.y_segment, sr=self.sr, bins_per_octave=24)

        # chroma_vals is the amount of each pitch class present in this time interval
        self.chroma_vals = []
        for i in range(12):
            self.chroma_vals.append(np.sum(self.chromograph[i]))
        pitches = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        # dictionary relating pitch names to the associated intensity in the song
        self.keyfreqs = {pitches[i]: self.chroma_vals[i] for i in range(12)}

        keys = [pitches[i] + ' major' for i in range(12)] + [pitches[i] + ' minor' for i in range(12)]

        # use of the Krumhansl-Schmuckler key-finding algorithm, which compares the chroma
        # data above to typical profiles of major and minor keys:
        maj_profile = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
        min_profile = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]

        # finds correlations between the amount of each pitch class in the time interval and the above profiles,
        # starting on each of the 12 pitches. then creates dict of the musical keys (major/minor) to the correlation
        self.min_key_corrs = []
        self.maj_key_corrs = []
        for i in range(12):
            key_test = [self.keyfreqs.get(pitches[(i + m) % 12]) for m in range(12)]
            # correlation coefficients (strengths of correlation for each key)
            self.maj_key_corrs.append(round(np.corrcoef(maj_profile, key_test)[1, 0], 3))
            self.min_key_corrs.append(round(np.corrcoef(min_profile, key_test)[1, 0], 3))

        # names of all major and minor keys
        self.key_dict = {**{keys[i]: self.maj_key_corrs[i] for i in range(12)},
                         **{keys[i + 12]: self.min_key_corrs[i] for i in range(12)}}

        # this attribute represents the key determined by the algorithm
        self.key = max(self.key_dict, key=self.key_dict.get)
        self.bestcorr = max(self.key_dict.values())

        # this attribute represents the second-best key determined by the algorithm,
        # if the correlation is close to that of the actual key determined
        self.altkey = None
        self.altbestcorr = None

        for key, corr in self.key_dict.items():
            if corr > self.bestcorr * 0.9 and corr != self.bestcorr:
                self.altkey = key
                self.altbestcorr = corr

    # prints the relative prominence of each pitch class
    def print_chroma(self):
        self.chroma_max = max(self.chroma_vals)
        for key, chrom in self.keyfreqs.items():
            print(key, '\t', f'{chrom / self.chroma_max:5.3f}')

    # prints the correlation coefficients associated with each major/minor key
    def corr_table(self):
        for key, corr in self.key_dict.items():
            print(key, '\t', f'{corr:6.3f}')

    # printout of the key determined by the algorithm; if another key is close, that key is mentioned
    def print_key(self):
        print("likely key: ", max(self.key_dict, key=self.key_dict.get), ", correlation: ", self.bestcorr, sep='')
        likely_key = max(self.key_dict, key=self.key_dict.get)
        alt_key = self.altkey
        if self.altkey is not None:
            print("also possible: ", self.altkey, ", correlation: ", self.altbestcorr, sep='')
        return likely_key, alt_key

    # prints a chromagram of the file, showing the intensity of each pitch class over time
    def chromagram(self, title=None):
        C = librosa.feature.chroma_cqt(y=self.waveform, sr=sr, bins_per_octave=24)
        plt.figure(figsize=(12, 4))
        librosa.display.specshow(C, sr=sr, x_axis='time', y_axis='chroma', vmin=0, vmax=1)
        if title is None:
            plt.title('Chromagram')
        else:
            plt.title(title)
        plt.colorbar()
        plt.tight_layout()
        plt.show()


class Tonality(object):
    def __init__(self):
        pitches = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        self.keys = [pitches [i] + ' major' for i in range(12)] + [pitches [i] + ' minor' for i in range(12)]

        self.chords_for_keys = {
            'С major': {1:'C', 2:'Dm', 3:'Em', 4:'F', 5:'G', 6:'Am', 7:'B[dim]'},
            'С# major': {1:'C#', 2:'D#m', 3:'Fm', 4:'F#', 5:'G#', 6:'A#m', 7:'C[dim]'},
            'D major': {1:'D', 2:'Em', 3:'F#m', 4:'G', 5:'A', 6:'Bm', 7:'C#[dim]'}, 
            'D# major': {1:'D#', 2:'Fm', 3:'Gm', 4:'G#', 5:'A#', 6:'Cm', 7:'D[dim]'},
            'E major': {1:'E', 2:'F#m', 3:'G#m', 4:'A', 5:'B', 6:'C#m', 7:'D#[dim]'},
            'F major': {1:'F', 2:'Gm', 3:'Am', 4:'A#', 5:'C', 6:'Dm', 7:'E[dim]'},
            'F# major': {1:'F#', 2:'G#m', 3:'A#m', 4:'B', 5:'C#', 6:'D#m', 7:'F[dim]'},
            'G major': {1:'G', 2:'Am', 3:'Bm', 4:'C', 5:'D', 6:'Em', 7:'F#[dim]'},
            'G# major': {1:'G#', 2:'A#m', 3:'Cm', 4:'C#', 5:'D#', 6:'Fm', 7:'G[dim]'},
            'A major': {1:'A', 2:'Bm', 3:'C#m', 4:'D', 5:'E', 6:'F#m', 7:'G#[dim]'},
            'A# major': {1:'A#', 2:'Cm', 3:'Dm', 4:'D#', 5:'F', 6:'Gm', 7:'A[dim]'},
            'B major': {1:'B', 2:'C#m', 3:'D#m', 4:'E', 5:'F#', 6:'G#m', 7:'A#[dim]'},

            'С minor': {1:'Cm', 2:'D[dim]', 3:'D#', 4:'Fm', 5:'Gm', 6:'G#', 7:'A#'},
            'С# minor': {1:'C#m', 2:'D#[dim]', 3:'E', 4:'F#m', 5:'G#m', 6:'A', 7:'B'},
            'D minor': {1:'Dm', 2:'E[dim]', 3:'F', 4:'Gm', 5:'Am', 6:'A#', 7:'C'},
            'D# minor': {1:'D#m', 2:'F[dim]', 3:'F#', 4:'G#m', 5:'A#m', 6:'B', 7:'C#'},
            'E minor': {1:'Em', 2:'F#[dim]', 3:'G', 4:'Am', 5:'Bm', 6:'C', 7:'D'},
            'F minor': {1:'Fm', 2:'G[dim]', 3:'G#', 4:'A#m', 5:'Cm', 6:'C#', 7:'D#'},
            'F# minor': {1:'F#m', 2:'G#[dim]', 3:'A', 4:'Bm', 5:'C#m', 6:'D', 7:'E'},
            'G minor': {1:'Gm', 2:'A[dim]', 3:'A#', 4:'Cm', 5:'Dm', 6:'D#', 7:'F'},
            'G# minor': {1:'G#m', 2:'A#[dim]', 3:'B', 4:'C#m', 5:'D#m', 6:'E', 7:'F#'},
            'A minor': {1:'Am', 2:'B[dim]', 3:'C', 4:'Dm', 5:'Em', 6:'F', 7:'G'},
            'A# minor': {1:'A#m', 2:'C[dim]', 3:'C#', 4:'D#m', 5:'Fm', 6:'F#', 7:'G#'},
            'B minor': {1:'Bm', 2:'C#[dim]', 3:'D', 4:'Em', 5:'F#m', 6:'G', 7:'A'},
        }

    def build_chords(self, keys, str_chords, song_key):
        str_chords = '\n[-----'
        for key in keys:
            str_chords += f'--{key}--'
        str_chords += '-----]\n'

        for i in keys:
            single_chord = self.chords_for_keys[song_key][i]
            str_chords +=  f'[{i}]: ' + single_chord + ', '
        str_chords += '\n[------------------------------]\n'
        return str_chords
    
    def get_chords(self, song_key):
        keys = self.chords_for_keys[song_key].keys()
        chords = ''
        return self.build_chords(keys, chords, song_key)
    
    def get_random_chords(self):
        random_key = random.choice(self.keys)
        return random_key, self.get_chords(random_key)

    def get_major_chord_progression(self, song_key):
        str_progression = ''

        # I V iv IV
        keys = {1, 5, 6, 4}
        str_progression += self.build_chords(keys, str_progression, song_key)

        # I vi IV V
        keys = {1, 6, 4, 5}
        str_progression += self.build_chords(keys, str_progression, song_key)

        # I IV V
        keys = {1, 4, 5}
        str_progression += self.build_chords(keys, str_progression, song_key)

        # ii V I
        keys = {1, 6, 4, 5}
        str_progression += self.build_chords(keys, str_progression, song_key)
        
        
        return str_progression

    def get_minor_chord_progression(self, song_key):
        str_progression = ''

        # I V iv IV
        keys = {1, 5, 6, 4}
        str_progression += self.build_chords(keys, str_progression, song_key)     
        
        return str_progression
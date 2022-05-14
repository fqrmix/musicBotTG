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
        keys = [pitches [i] + ' major' for i in range(12)] + [pitches [i] + ' minor' for i in range(12)]

        chords_for_keys = {
            'С major': {1:'C', 2:'Dm', 3:'Em', 4:'F', 5:'G', 6:'Am', 7:'Bm[dim]'},
            'С# major': {1:'C#', 2:'D#m', 3:'Fm', 4:'F#', 5:'G#', 6:'A#m', 7:'Cm[dim]'},
            'D major': {1:'D', 2:'Em', 3:'F#m', 4:'G', 5:'A', 6:'Bm', 7:'C#m[dim]'}, 
            'D# major': {1:'D#', 2:'Fm', 3:'Gm', 4:'G#', 5:'A#', 6:'Cm', 7:'Dm[dim]'},
            'E major': {1:'E', 2:'F#m', 3:'G#m', 4:'A', 5:'B', 6:'C#m', 7:'D#m[dim]'},
            'F major': {1:'F', 2:'Gm', 3:'Am', 4:'A#', 5:'C', 6:'Dm', 7:'Em[dim]'},
            'F# major': '',
            'G major': '',
            'G# major': '',
            'A major': '',
            'A# major': '',
            'B major': '',

            'С minor': 'Cm Ddim Eb Fm Gm Ab Bb',
            'С# minor': 'C#m D#dim E F#m G#m A B',
            'D minor': 'Dm Edim F Gm Am Bb C',
            'D# minor': 'D#m Fdim F# G#m A#m B C#',
            'E minor': 'Em F#dim G Am Bm C D',
            'F minor': 'Fm Gdim Ab Bbm Cm Db Eb',
            'F# minor': 'F#m G#dim A Bm C#m D E',
            'G minor': 'Gm Adim Bb Cm Dm Eb F',
            'G# minor': 'G#m A#dim B C#m D#m E F#',
            'A minor': 'Am Bdim C Dm Em F G',
            'A# minor': 'A#m Cdim C# D#m E#m F#	G#',
            'B minor': 'Bm C#dim D Em F#m G A',
        }

        print(keys)


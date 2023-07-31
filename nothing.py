from TTS.api import TTS

tts = TTS(model_name='tts_models/en/ljspeech/glow-tts')
print(tts.is_multi_speaker)
tts.tts_to_file(text="The Cassini spacecraft was a NASA robotic probe that was launched in 1997 with the mission to "
                     "study the planet Saturn and its moons. It was a joint project managed by NASA, the European "
                     "Space Agency (ESA), and the Italian Space Agency (ASI). Cassini's main objective was to provide "
                     "in-depth exploration and scientific observations of Saturn and its surrounding environment. It "
                     "carried a suite of sophisticated instruments and cameras designed to study the atmosphere, "
                     "rings, and magnetic field of Saturn, as well as its collection of moons, including Titan and "
                     "Enceladus. The spacecraft reached Saturn in 2004, and it spent over 13 years orbiting the "
                     "planet and making incredible discoveries. Some of its major achievements include: 1. "
                     "Exploration of Saturn's rings: Cassini provided detailed images and data on the structure, "
                     "composition, and dynamics of Saturn's iconic rings. It discovered intricacies like gaps, waves, "
                     "and other features within the rings that were previously unknown. 2. Investigation of Saturn's "
                     "moons: Cassini performed extensive studies of Saturn's moons, particularly Titan and Enceladus. "
                     "It discovered that Titan has a thick atmosphere and revealed evidence of lakes, rivers, "
                     "and a complex weather cycle on its surface. It also found that Enceladus has geysers spewing "
                     "water vapor and complex organic molecules from beneath its icy crust, indicating the potential "
                     "for habitable conditions. 3. Study of Saturn's magnetosphere: Cassini provided detailed "
                     "measurements of Saturn's magnetosphere, the region of space surrounding the planet influenced "
                     "by its magnetic field. It observed the interactions between Saturn's magnetic field and the "
                     "solar wind, shedding light on the processes involved. The mission ended in September 2017 with "
                     "the spacecraft intentionally plunging into Saturn's atmosphere. This controlled maneuver "
                     "ensured that Cassini would not contaminate any of Saturn's potentially habitable moons with "
                     "Earthly microbes. Overall, the Cassini mission greatly expanded our understanding of Saturn, "
                     "its rings, moons, and their interactions. It revolutionized our knowledge of these cosmic "
                     "phenomena, leaving a lasting impact on planetary science.", gpu=False, progress_bar=False)

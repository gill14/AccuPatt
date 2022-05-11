from accupatt.models.passData import Pass
from accupatt.models.seriesData import SeriesData
from accupatt.models.sprayCard import SprayCard


class SprayCardComposite(SprayCard):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Must keep these lists for appending to as building from individual spray cards
        self.drop_dia_um = []
        self.drop_vol_um3 = []
        # Must keep this for building sum area of individual spray cards
        self.area_in2 = 0.0

    def buildFromCard(self, card: SprayCard):
        self._buildFromList([card])

    def buildFromPass(self, passData: Pass):
        self._buildFromList(passData.cards.card_list)

    def buildFromSeries(self, seriesData: SeriesData):
        cards: list[SprayCard] = []
        for p in seriesData.passes:
            if p.cards_include_in_composite:
                for card in p.cards.card_list:
                    cards.append(card)
        self._buildFromList(cards)

    def _buildFromList(self, cards: list[SprayCard]):
        # Build composite from valid cards
        for card in cards:
            if not card.has_image:
                continue
            if not card.include_in_composite:
                continue
            self.area_px2 += card.area_px2
            self.area_in2 += card.stats._px2_to_in2(card.area_px2)
            dd, dv = card.stats.get_droplet_diameters_and_volumes()
            self.drop_dia_um.extend(dd)
            self.drop_vol_um3.extend(dv)
            self.stain_areas_all_px2.extend(card.stain_areas_all_px2)
            self.stain_areas_valid_px2.extend(card.stain_areas_valid_px2)
        # Sort the dia and vol lists before computing dv's
        self.drop_dia_um.sort()
        self.drop_vol_um3.sort()
        # Set the dv vals in composite stats object for future use
        self.stats.set_volumetric_stats(self.drop_dia_um, self.drop_vol_um3)

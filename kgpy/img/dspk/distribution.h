/*
 * distribution.h
 *
 *  Created on: Jun 28, 2018
 *      Author: byrdie
 */

#ifndef KGPY_IMG_DSPK_DISTRIBUTION_H_
#define KGPY_IMG_DSPK_DISTRIBUTION_H_

#include <kgpy/img/dspk/util.h>
#include <math.h>


namespace kgpy {

namespace img {

namespace dspk {

void calc_histogram(DB * db, float * lmed, int axis);
void calc_cumulative_distribution(DB * db, int axis);

void init_histogram(DB * db);
void init_cumulative_distribution(DB * db);

void calc_intensity_histogram(DB * db);
void calc_intensity_cumulative_distribution(DB * db);

float hist2data(int hval, float m_min, float m_max, int nbins);
int data2hist(float dval, float m_min, float m_max, int nbins);

}

}

}


#endif /* KGPY_IMG_DSPK_DISTRIBUTION_H_ */

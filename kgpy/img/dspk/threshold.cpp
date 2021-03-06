/*
 * threshold.cpp
 *
 *  Created on: Jun 28, 2018
 *      Author: byrdie
 */

#include <kgpy/img/dspk/threshold.h>

namespace kgpy {

namespace img {

namespace dspk {

void calc_thresh(DB * db, float tmin, float tmax, int axis) {

	// start by calculating the exact threshold based off of histogram columns
	calc_exact_thresh(db, tmin, tmax, axis);

	// extrapolate threshold into statistically insignificant areas
	calc_extrap_thresh(db, tmin, tmax, axis);

}

void calc_exact_thresh(DB * db, float tmin, float tmax, int axis){

	float * cumd = db->cumd;
	float * t1 = db->t1;
	float * t9 = db->t9;
	dim3 hsz = db->hsz;

	// compute histogram strides
	int hx = 1;
	int hy = hx * hsz.x;
	int hz = hy * hsz.y;

	// compute threshold strides
	int tx = 1;
	int tz = tx * hsz.x;

	// determine initial threshold array, ignoring counts
#pragma acc parallel loop present(cumd), present(t1), present(t9)
	for(int x = 0; x < hsz.x; x++){

		// index of threshold array
		int T = tz * axis + tx * x;

		//initialize thresholds
		t1[T] = x;
		t9[T] = x - 1;

		// locate lower threshold
		int y;
#pragma acc loop seq
		for(y = 0; y < hsz.y; y++){

			// check if above lower threshold
			int H = hz * axis + hy * y + hx * x;
			float c = cumd[H];
			if (c > tmin) {
				t9[T] = y - 1;
				break;
			}

		}

		// locate upper threshold, starting from where we left off in the last loop
#pragma acc loop seq
		for(int Y = y; Y < hsz.y; Y++){

			// check if above lower threshold
			int H = hz * axis + hy * Y + hx * x;
			float c = cumd[H];
			if (c > tmax) {
				t1[T] = Y;
				break;
			}

		}

	}

}

void calc_extrap_thresh(DB * db, float tmin, float tmax, int axis){

	// load from database
	float * t9 = db->t9;
	float * t1 = db->t1;

	int x0 = calc_hist_center(db, axis);

	// extrapolate threshold by slicing histogram along threshold
	float theta_min = median_extrapolation(db, t9, tmin, x0, axis);
	float theta_max = median_extrapolation(db, t1, tmax, x0, axis);

	// save the extrapolated trheshold curve to arrays
	apply_extrap_thresh(db, t9, tmin, x0, theta_min, axis);
	apply_extrap_thresh(db, t1, tmax, x0, theta_max, axis);




}

void apply_extrap_thresh(DB * db, float * t, float thresh, int x0, float theta, int axis){

	// load from database
	float * cnts = db->cnts;
	dim3 hsz = db->hsz;

	// compute threshold strides
	int tx = 1;
	int tz = tx * hsz.x;

	// find minimum counts for statistical significance
	int min_cnts = min_samples(thresh);

	// replace all statistically insignificant points with extrapolated line
#pragma acc parallel loop present(t), present(cnts)
	for(int x = 0; x < hsz.x; x++){

		// grab y-value at most statistically significant point
		int y0 = t[tz * axis + tx * x0];

		float m = tan(theta);
		float b = calc_intercept(x0, y0, m);

		int T = tz * axis + tx * x;

		// if point is not statistically significant
		if(cnts[T] < min_cnts) {
//			if(x >= x0) {	// above center of histogram
//				t[T] = m * x + b;
//			} else {		// below center of histogram, reflect line about y=x
//				float M = 1 / m;
//				float B = y0 - M * x0;
//				t[T] = M * x + B;
//			}

			t[T] = m * x + b;

			// make sure upper thresh does not cross lower thresh
			t[T] = fmax(fmin(t[T], hsz.y - 1), 0); // make sure we don't cross top/bottom of histogram

		}

	}

}

float median_extrapolation(DB * db, float * t, float thresh, int x0, int axis){

	// load from database
	float * cnts = db->cnts;
	dim3 hsz = db->hsz;
	dim3 tsz = db->tsz;

	// compute threshold strides
	int tx = 1;
	int tz = tx * tsz.x;

	// find minimum counts for statistical significance
	int min_cnts = min_samples(thresh);

	// extrapolate slope of threshold
	for (float theta = 0.0f; theta < M_PI/2; theta += M_PI/(hsz.x + hsz.y)){

		float lsum = 0;
		float usum = 0;

#pragma acc parallel loop reduction(+:usum,lsum) present(cnts), present(t)
		for(int x = 0; x < hsz.x; x++){

			int T = tz * axis + tx * x;
			float Y = t[T];

			// grab y-value at most statistically significant point
			int y0 = t[tz * axis + tx * x0];

			float m = tan(theta);
			float b = calc_intercept(x0, y0, m);
			float y = m * x + b;

			if(cnts[T] > min_cnts) {
				if (Y > y) {
					usum++;
				} else {
					lsum++;
				}
			}

		}

		float ratio =  lsum / (usum + lsum);

		if (ratio >= 0.50) {
			return theta;
		}
	}

	return 0.0;

}

void calc_intensity_thresh(DB * db, float tmin, float tmax){

	float * icmd = db->icmd;
	dim3 hsz = db->hsz;

	float i1 = 0.0f;
	float i9 = 0.0f;

	bool found = false;

		// locate lower threshold
#pragma acc kernels present(icmd) copy(found)
		for(int x = 0; x < hsz.x; x++){

			// check if above lower threshold
			float c = icmd[x];
			if ((c > tmin) and (not found)) {
				i9 = x - 1;
				found = true;
			}

		}

		found = false;

		// locate upper threshold, starting from where we left off in the last loop
#pragma acc kernels present(icmd) copy(found)
		for(int x = 0; x < hsz.x; x++){

			// check if above lower threshold
			float c = icmd[x];
			if ((c > tmax) and (not found)) {
				i1 = (float) x;
				found = true;
			}

		}

	db->i1 = i1;
	db->i9 = i9;

	printf("%f %f\n", i9, i1);

}

int calc_hist_center(DB * db, int axis) {

	// load info from database
	float * cnts = db->cnts;
	dim3 tsz = db->tsz;
	int max_ind = 0;

	// compute threshold strides
	int tx = 1;
	int tz = tx * tsz.x;

	// find most statstically significant threshold
	float max_cnt = -10.0f;
	//#pragma acc update host(cnts[0:tsz.xyz])

	// calc max value
#pragma acc parallel loop reduction(max:max_cnt) present(cnts)
	for(int X = 0; X < tsz.x; X++){

		int T = tz * axis + tx * X;

		//			printf("%f\n", cnts[T]);

		if(cnts[T] > max_cnt) {
			max_cnt = cnts[T];
		}
	}

	// calc index of max value
#pragma acc parallel loop present(cnts) copyout(max_ind)
	for(int X = 0; X < tsz.x; X++){

		int T = tz * axis + tx * X;

		if(cnts[T] == max_cnt) {
			max_ind = X;
		}

	}


	return max_ind;


}

float pts2slope(int x0, int y0, int x1, int y1) {

	float dy = (float) (y1 - y0);
	float dx = (float) (x1 - x0);

	return dy / dx;

}

float calc_intercept(int x0, int y0, float m){

	return y0 - m * x0;

}

int min_samples(float thresh){

	// compute how many counts are required for adequate statistics
	float interval = fmin(1.0f - thresh, thresh);
	float sigma = 15.0f;	// how many points need to be outside the confidence interval
	int min_cnts = sigma / interval;

	return min_cnts;

}

}

}

}


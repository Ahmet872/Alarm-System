import React, { useState } from 'react';
import { useForm, SubmitHandler } from 'react-hook-form';
import toast from 'react-hot-toast';
import {
  createAlarm,
  AlarmData,
  AlarmParams,
  APIError
} from '../lib/api';

const AlarmForm: React.FC = () => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const { 
    register, 
    handleSubmit, 
    watch, 
    formState: { errors }, 
    reset 
  } = useForm<AlarmData>({
    defaultValues: {
      asset_class: undefined,
      asset_symbol: '',
      alarm_type: undefined,
      email: '',
      params: {}
    }
  });

  const selectedAlarmType = watch('alarm_type');

  const onSubmit: SubmitHandler<AlarmData> = async (formData) => {
    setIsSubmitting(true);

    try {
      let params: AlarmParams = {};

      if (formData.alarm_type === 'price') {
        const targetPrice = Number(formData.params?.target_price);
        const direction = formData.params?.direction || 'above';
        if (isNaN(targetPrice) || targetPrice <= 0) {
          throw new Error('Invalid price value');
        }
        params = { target_price: targetPrice, direction };
      } else if (formData.alarm_type === 'rsi') {
        const period = Number(formData.params?.period);
        const threshold = Number(formData.params?.threshold);
        if (isNaN(period) || period < 1 || period > 100) {
          throw new Error('Invalid RSI period');
        }
        if (isNaN(threshold) || threshold < 0 || threshold > 100) {
          throw new Error('Invalid RSI threshold');
        }
        params = { period, threshold };
      } else if (formData.alarm_type === 'bollinger') {
        const period = Number(formData.params?.period);
        const stdDev = Number(formData.params?.std_dev);
        if (isNaN(period) || period < 1 || period > 100) {
          throw new Error('Invalid Bollinger period');
        }
        if (isNaN(stdDev) || stdDev <= 0 || stdDev > 10) {
          throw new Error('Invalid standard deviation');
        }
        params = { period, std_dev: stdDev };
      }

      const response = await createAlarm({
        ...formData,
        params
      });

      toast.success('Alarm created successfully!', {
        duration: 3000,
        position: 'top-right',
      });
      reset();
    } catch (err) {
      const errorMessage = err instanceof APIError ? err.message : 'Failed to create alarm';
      toast.error(`Error: ${errorMessage}`, {
        duration: 4000,
        position: 'top-right',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Asset Class Selection */}
      <div>
        <label className="block text-sm font-semibold text-gray-900 mb-2">
          Asset Class
        </label>
        <select
          {...register('asset_class', { required: 'Asset class is required' })}
          className={`w-full px-4 py-3 rounded-lg border-2 transition-colors ${
            errors.asset_class
              ? 'border-red-500 focus:border-red-600'
              : 'border-gray-300 focus:border-blue-500'
          }`}
        >
          <option value="">Select Asset Class</option>
          <option value="crypto">Cryptocurrency</option>
          <option value="forex">Forex</option>
          <option value="stock">Stock</option>
        </select>
        {errors.asset_class && (
          <p className="text-red-500 text-sm mt-2 flex items-center gap-1">
            <span>*</span> {errors.asset_class.message}
          </p>
        )}
      </div>

      {/* Asset Symbol Input */}
      <div>
        <label className="block text-sm font-semibold text-gray-900 mb-2">
          Asset Symbol
        </label>
        <input
          type="text"
          {...register('asset_symbol', {
            required: 'Asset symbol is required',
            pattern: {
              value: /^[A-Za-z0-9-/]+$/,
              message: 'Invalid symbol format'
            }
          })}
          placeholder="e.g., BTC-USD, EUR/USD, AAPL"
          className={`w-full px-4 py-3 rounded-lg border-2 transition-colors ${
            errors.asset_symbol
              ? 'border-red-500 focus:border-red-600'
              : 'border-gray-300 focus:border-blue-500'
          }`}
        />
        {errors.asset_symbol && (
          <p className="text-red-500 text-sm mt-2 flex items-center gap-1">
            <span>*</span> {errors.asset_symbol.message}
          </p>
        )}
        <p className="text-gray-500 text-xs mt-2">
          Examples: BTC-USD (crypto) • EUR/USD (forex) • AAPL (stock)
        </p>
      </div>

      {/* Alarm Type Selection */}
      <div>
        <label className="block text-sm font-semibold text-gray-900 mb-2">
          Alarm Type
        </label>
        <select
          {...register('alarm_type', { required: 'Alarm type is required' })}
          className={`w-full px-4 py-3 rounded-lg border-2 transition-colors ${
            errors.alarm_type
              ? 'border-red-500 focus:border-red-600'
              : 'border-gray-300 focus:border-blue-500'
          }`}
        >
          <option value="">Select Alarm Type</option>
          <option value="price">Price Alert</option>
          <option value="rsi">RSI Indicator</option>
          <option value="bollinger">Bollinger Bands</option>
        </select>
        {errors.alarm_type && (
          <p className="text-red-500 text-sm mt-2 flex items-center gap-1">
            <span>*</span> {errors.alarm_type.message}
          </p>
        )}
      </div>

      {/* Dynamic Parameter Fields */}
      {selectedAlarmType && (
        <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
          {/* Price Alert Parameters */}
          {selectedAlarmType === 'price' && (
            <div className="space-y-4">
              <h3 className="font-semibold text-gray-900 mb-4">
                Price Alert Parameters
              </h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">
                  Target Price
                </label>
                <input
                  type="number"
                  step="any"
                  {...register('params.target_price', {
                    required: 'Target price is required',
                    min: { value: 0, message: 'Price must be positive' }
                  })}
                  placeholder="e.g., 50000"
                  className="w-full px-4 py-2 rounded-lg border border-gray-300 focus:border-blue-500"
                />
                {errors.params?.target_price && (
                  <p className="text-red-500 text-sm mt-1">
                    {errors.params.target_price.message}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">
                  Direction
                </label>
                <select
                  {...register('params.direction')}
                  className="w-full px-4 py-2 rounded-lg border border-gray-300 focus:border-blue-500"
                >
                  <option value="above">Above (greater than or equal)</option>
                  <option value="below">Below (less than or equal)</option>
                </select>
              </div>
            </div>
          )}

          {/* RSI Alert Parameters */}
          {selectedAlarmType === 'rsi' && (
            <div className="space-y-4">
              <h3 className="font-semibold text-gray-900 mb-4">
                RSI Parameters
              </h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">
                  Period (1-100)
                </label>
                <input
                  type="number"
                  {...register('params.period', {
                    required: 'Period is required',
                    min: { value: 1, message: 'Min: 1' },
                    max: { value: 100, message: 'Max: 100' }
                  })}
                  placeholder="14"
                  className="w-full px-4 py-2 rounded-lg border border-gray-300 focus:border-blue-500"
                />
                {errors.params?.period && (
                  <p className="text-red-500 text-sm mt-1">
                    {errors.params.period.message}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">
                  Threshold (0-100)
                </label>
                <input
                  type="number"
                  {...register('params.threshold', {
                    required: 'Threshold is required',
                    min: { value: 0, message: 'Min: 0' },
                    max: { value: 100, message: 'Max: 100' }
                  })}
                  placeholder="30"
                  className="w-full px-4 py-2 rounded-lg border border-gray-300 focus:border-blue-500"
                />
                {errors.params?.threshold && (
                  <p className="text-red-500 text-sm mt-1">
                    {errors.params.threshold.message}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Bollinger Bands Parameters */}
          {selectedAlarmType === 'bollinger' && (
            <div className="space-y-4">
              <h3 className="font-semibold text-gray-900 mb-4">
                Bollinger Bands Parameters
              </h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">
                  Period (1-100)
                </label>
                <input
                  type="number"
                  {...register('params.period', {
                    required: 'Period is required',
                    min: { value: 1, message: 'Min: 1' }
                  })}
                  placeholder="20"
                  className="w-full px-4 py-2 rounded-lg border border-gray-300 focus:border-blue-500"
                />
                {errors.params?.period && (
                  <p className="text-red-500 text-sm mt-1">
                    {errors.params.period.message}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">
                  Std Dev (0-10)
                </label>
                <input
                  type="number"
                  step="0.1"
                  {...register('params.std_dev', {
                    required: 'Std dev is required',
                    min: { value: 0.1, message: 'Min: 0.1' }
                  })}
                  placeholder="2"
                  className="w-full px-4 py-2 rounded-lg border border-gray-300 focus:border-blue-500"
                />
                {errors.params?.std_dev && (
                  <p className="text-red-500 text-sm mt-1">
                    {errors.params.std_dev.message}
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Email Address Input */}
      <div>
        <label className="block text-sm font-semibold text-gray-900 mb-2">
          Email Address
        </label>
        <input
          type="email"
          {...register('email', {
            required: 'Email is required',
            pattern: {
              value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
              message: 'Invalid email address'
            }
          })}
          placeholder="your@email.com"
          className={`w-full px-4 py-3 rounded-lg border-2 transition-colors ${
            errors.email
              ? 'border-red-500 focus:border-red-600'
              : 'border-gray-300 focus:border-blue-500'
          }`}
        />
        {errors.email && (
          <p className="text-red-500 text-sm mt-2 flex items-center gap-1">
            <span>*</span> {errors.email.message}
          </p>
        )}
      </div>

      {/* Form Submission Button */}
      <button
        type="submit"
        disabled={isSubmitting}
        className={`w-full py-3 px-6 rounded-lg font-semibold text-white transition-all duration-200 flex items-center justify-center gap-2 ${
          isSubmitting
            ? 'bg-gray-400 cursor-not-allowed opacity-75'
            : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 active:scale-95'
        }`}
      >
        <span>{isSubmitting ? 'Creating Alarm...' : 'Create Alarm'}</span>
      </button>

      {/* Information Banner */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-sm text-green-800">
        <p className="flex items-start gap-2">
          <span>Info:</span>
          <span>Your alarm will be monitored 24/7 and you will receive an email notification when the condition is met.</span>
        </p>
      </div>
    </form>
  );
};

export default AlarmForm;
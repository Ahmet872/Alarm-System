import React, { useState, useEffect } from 'react';
import { useForm, SubmitHandler } from 'react-hook-form';
import { 
  createAlarm, 
  getAssets, 
  AlarmData, 
  AlarmParams, 
  APIError,
  AssetClass,
  AlarmType 
} from '../lib/api';

const AlarmForm: React.FC = () => {
  const [assets, setAssets] = useState<string[]>([]);
  const [assetsLoading, setAssetsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState<string>('');
  
  const { register, handleSubmit, watch, formState: { errors }, setValue, reset } = useForm<AlarmData>({
    defaultValues: {
      asset_class: undefined,
      asset_symbol: '',
      alarm_type: undefined,
      email: '',
      params: {}
    }
  });
  
  const selectedAssetClass = watch('asset_class');
  const selectedAlarmType = watch('alarm_type');
  const selectedAssetSymbol = watch('asset_symbol');
  
  useEffect(() => {
    if (selectedAssetClass) {
      setAssetsLoading(true);
      getAssets(selectedAssetClass)
        .then(data => setAssets(data.assets))
        .catch(error => {
          console.error('Error fetching assets:', error);
          setAssets([]);
          setErrorMessage('Failed to load assets');
        })
        .finally(() => setAssetsLoading(false));
    } else {
      setAssets([]);
    }
    setValue('asset_symbol', '');
  }, [selectedAssetClass, setValue]);
  
  const onSubmit: SubmitHandler<AlarmData> = async (formData) => {
    setIsSubmitting(true);
    setErrorMessage('');
    try {
      let params: AlarmParams = {};
      
      if (formData.alarm_type === 'price') {
        const targetPrice = Number(formData.params?.target_price);
        if (isNaN(targetPrice)) {
          throw new Error('Invalid target price value');
        }
        params = { target_price: targetPrice };
      }
      else if (formData.alarm_type === 'rsi') {
        const period = Number(formData.params?.period);
        const threshold = Number(formData.params?.threshold);
        if (isNaN(period) || isNaN(threshold)) {
          throw new Error('Invalid RSI parameters');
        }
        params = { period, threshold };
      }
      else if (formData.alarm_type === 'bollinger') {
        const period = Number(formData.params?.period);
        const stdDev = Number(formData.params?.std_dev);
        if (isNaN(period) || isNaN(stdDev)) {
          throw new Error('Invalid Bollinger parameters');
        }
        params = { period, std_dev: stdDev };
      }

      const payload: AlarmData = {
        ...formData,
        params
      };

      console.log('Sending payload:', payload);
      const response = await createAlarm(payload);
      console.log('Server response:', response);
      setSubmitStatus('success');
      reset(); // Form başarılı olunca sıfırla
      
    } catch (error) {
      console.error('Error submitting alarm:', error);
      setSubmitStatus('error');
      if (error instanceof APIError) {
        try {
          const errorDetail = JSON.parse(error.message);
          setErrorMessage(errorDetail.detail || 'API Error occurred');
        } catch {
          setErrorMessage(error.message);
        }
      } else {
        setErrorMessage(error instanceof Error ? error.message : 'Unknown error occurred');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 bg-white p-6 rounded-lg shadow">
      {/* Asset Class Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700">Asset Class</label>
        <select
          {...register('asset_class', { required: 'Asset class is required' })}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
        >
          <option value="">Select Asset Class</option>
          <option value="crypto">Cryptocurrency</option>
          <option value="forex">Forex</option>
          <option value="stock">Stock</option>
        </select>
        {errors.asset_class && (
          <p className="mt-1 text-sm text-red-600">{errors.asset_class.message}</p>
        )}
      </div>

      {/* Asset Symbol Selection */}
      {selectedAssetClass && (
        <div>
          <label className="block text-sm font-medium text-gray-700">Asset Symbol</label>
          <select
            {...register('asset_symbol', { required: 'Asset symbol is required' })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            disabled={assetsLoading}
          >
            <option value="">Select Asset</option>
            {assetsLoading ? (
              <option disabled>Loading assets...</option>
            ) : (
              assets.map(asset => (
                <option key={asset} value={asset}>{asset}</option>
              ))
            )}
          </select>
          {errors.asset_symbol && (
            <p className="mt-1 text-sm text-red-600">{errors.asset_symbol.message}</p>
          )}
        </div>
      )}

      {/* Alarm Type Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700">Alarm Type</label>
        <select
          {...register('alarm_type', { required: 'Alarm type is required' })}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
        >
          <option value="">Select Alarm Type</option>
          <option value="price">Price</option>
          <option value="rsi">RSI</option>
          <option value="bollinger">Bollinger Bands</option>
        </select>
        {errors.alarm_type && (
          <p className="mt-1 text-sm text-red-600">{errors.alarm_type.message}</p>
        )}
      </div>

      {/* Dynamic Parameters Based on Alarm Type */}
      {selectedAlarmType && (
        <div className="space-y-4">
          {selectedAlarmType === 'price' && (
            <div>
              <label className="block text-sm font-medium text-gray-700">Target Price</label>
              <input
                type="number"
                step="any"
                {...register('params.target_price', { 
                  required: 'Target price is required',
                  min: { value: 0, message: 'Price must be positive' }
                })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              />
              {errors.params?.target_price && (
                <p className="mt-1 text-sm text-red-600">{errors.params.target_price.message}</p>
              )}
            </div>
          )}

          {selectedAlarmType === 'rsi' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700">Period</label>
                <input
                  type="number"
                  {...register('params.period', { 
                    required: 'Period is required',
                    min: { value: 1, message: 'Period must be positive' }
                  })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                />
                {errors.params?.period && (
                  <p className="mt-1 text-sm text-red-600">{errors.params.period.message}</p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Threshold</label>
                <input
                  type="number"
                  {...register('params.threshold', { 
                    required: 'Threshold is required',
                    min: { value: 0, message: 'Threshold must be between 0 and 100' },
                    max: { value: 100, message: 'Threshold must be between 0 and 100' }
                  })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                />
                {errors.params?.threshold && (
                  <p className="mt-1 text-sm text-red-600">{errors.params.threshold.message}</p>
                )}
              </div>
            </>
          )}

          {selectedAlarmType === 'bollinger' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700">Period</label>
                <input
                  type="number"
                  {...register('params.period', { 
                    required: 'Period is required',
                    min: { value: 1, message: 'Period must be positive' }
                  })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                />
                {errors.params?.period && (
                  <p className="mt-1 text-sm text-red-600">{errors.params.period.message}</p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Standard Deviation</label>
                <input
                  type="number"
                  step="0.1"
                  {...register('params.std_dev', { 
                    required: 'Standard deviation is required',
                    min: { value: 0.1, message: 'Standard deviation must be positive' }
                  })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                />
                {errors.params?.std_dev && (
                  <p className="mt-1 text-sm text-red-600">{errors.params.std_dev.message}</p>
                )}
              </div>
            </>
          )}
        </div>
      )}

      {/* Email Input */}
      <div>
        <label className="block text-sm font-medium text-gray-700">Email</label>
        <input
          type="email"
          {...register('email', { 
            required: 'Email is required',
            pattern: {
              value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
              message: 'Invalid email address'
            }
          })}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
        />
        {errors.email && (
          <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
        )}
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isSubmitting}
        className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${
          isSubmitting
            ? 'bg-indigo-300 cursor-not-allowed'
            : 'bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500'
        }`}
      >
        {isSubmitting ? 'Setting Alarm...' : 'Set Alarm'}
      </button>

      {/* Error Messages */}
      {errorMessage && (
        <div className="mt-2 text-sm text-red-600">
          {errorMessage}
        </div>
      )}

      {/* Success Message */}
      {submitStatus === 'success' && (
        <div className="mt-2 text-sm text-green-600">
          Alarm set successfully! You will receive an email when the condition is met.
        </div>
      )}
    </form>
  );
};

export default AlarmForm;
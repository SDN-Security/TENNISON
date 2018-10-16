/*
 * Copyright 2015 Open Networking Laboratory
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package org.onosproject.ipfix;

/**
 * Abstract interface for an IP DataRecord.
 */
public class Data<T> {

    private String dataName;
    private Class<?> dataType;
    private T dataValue;

    public Data(String dataName, T dataValue) {
        this.dataName = dataName;
        this.dataType = dataValue.getClass();
        this.dataValue = dataValue;
    }

    public String getDataName() {
        return dataName;
    }

    public Class<?> getDataType() {
        return dataType;
    }

    public T getDataValue() {
        return dataValue;
    }
}
